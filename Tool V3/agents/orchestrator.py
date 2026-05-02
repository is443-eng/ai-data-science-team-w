"""
Central orchestrator for Agents 1–5 (Segment 2).

Execution order: Agent 1 (CDC tools) → Agents 2 & 3 in parallel → Agents 4 (state reporter) & 5 (national reporter) in parallel.

State data agent = Agent 2 (tools). National data agent = Agent 3 (tools). Agent 4 consumes Agent 2; Agent 5 consumes Agent 3.

Partial failure: tool or LLM errors become AgentResult.error with messages; other agents still run when possible.
Agent 4 is skipped if the state data agent (Agent 2) did not succeed.
"""
from __future__ import annotations

import json
import os
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from contracts.schemas import AgentContext, AgentResult, InsightQCResult, ToolOutput

from ollama_client import chat_completion, chat_completion_with_tools_openai
from prompts.loader import orchestrator_system

from .insight_quality import insight_qc_enabled, run_insight_qc
from tools._common import make_tool_output, tool_output_to_dataframe, utc_as_of
from tools.registry import run_tool as registry_run_tool
from utils.logging_config import get_logger
from utils.state_maps import state_to_abbr

logger = get_logger("orchestrator")

# Must match Segment 1 registry; fixed order for reproducible tests and logs.
TOOL_NAMES_ORDER = ("child_vax", "kindergarten_vax", "teen_vax", "wastewater", "nndss")


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _state_risk_extras_from_tools(
    tool_outputs: dict[str, ToolOutput],
    selected_state: str,
) -> tuple[str | None, str | None]:
    """
    Rebuild state risk JSON and optional snapshot from Agent 1 CDC payloads so Agent 3/5 match this run's data.

    Session ``state_risk_df`` can be missing or stale relative to the tools the orchestrator just ran.
    """
    from risk import format_state_risk_snapshot_line, get_state_risk_df

    kg = tool_output_to_dataframe(tool_outputs.get("kindergarten_vax"))
    nndss = tool_output_to_dataframe(tool_outputs.get("nndss"))
    ww = tool_output_to_dataframe(tool_outputs.get("wastewater"))
    ww_arg = ww if not ww.empty else None
    try:
        sr = get_state_risk_df(kg, nndss, ww_arg)
    except Exception as e:
        logger.warning("get_state_risk_df from Agent 1 tool outputs failed: %s", e)
        return None, None
    if sr is None or getattr(sr, "empty", True):
        return None, None
    cols = [
        c
        for c in (
            "state",
            "total_risk",
            "risk_tier",
            "cases_recent",
            "coverage",
            "wastewater_coverage",
        )
        if c in sr.columns
    ]
    if not cols:
        return None, None
    rec_json = sr[cols].to_json(orient="records")
    snap = None
    if (selected_state or "").strip():
        snap = format_state_risk_snapshot_line(sr, selected_state)
    return rec_json, snap


@dataclass
class RiskFields:
    """Risk/session fields from the Streamlit session. The orchestrator merges in state risk recomputed from Agent 1 tool payloads when available."""

    alarm_probability: float | None = None
    baseline_tier: str | None = None
    baseline_score: float | None = None
    """Overview gauge 0–100; same source as baseline tier (historical annual cases ratio)."""
    baseline_explanation: str | None = None
    """Preformatted text from get_baseline_risk_components for LLM attribution."""
    state_risk_snapshot: str | None = None
    """Preformatted row from state_risk_df for the selected state (coverage, cases, WW points)."""
    state_risk_records_json: str | None = None
    """JSON array of state_risk_df rows (subset of columns) for Agent 3 tool / fallback."""
    national_weekly_trend_json: str | None = None
    """Trailing national NNDSS weekly rows (year, week, cases) for Agent 3 temporal trend tool / fallback."""
    load_status: dict[str, str] = field(default_factory=dict)


# OpenAI function-calling: national agent may request ranked states (handler reads RiskFields-derived JSON in ctx.extra).
AGENT3_OPENAI_TOOLS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "get_state_risk_leaderboard",
            "description": (
                "Return the top US states ranked by this app's composite state risk score (kindergarten coverage, "
                "recent NNDSS cases, wastewater when available). Call when you need to name which states show the "
                "highest concern or recent activity in this model."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {
                        "type": "integer",
                        "description": "How many states to include from the top (1-51). Default 15.",
                        "minimum": 1,
                        "maximum": 51,
                    },
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_national_activity_trend",
            "description": (
                "Return how national NNDSS weekly measles cases in this app compare to the prior same-length window, "
                "to the same MMWR week band in prior years, and year-to-date vs prior years. Use when explaining "
                "whether the current period looks like a bad season or a bad year relative to recent history."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "weeks_compare": {
                        "type": "integer",
                        "description": "Weeks in each rolling window for recent vs prior comparison (default 12).",
                        "minimum": 4,
                        "maximum": 52,
                    },
                    "band_weeks": {
                        "type": "integer",
                        "description": "Length of the MMWR week band matched across years (default 8).",
                        "minimum": 2,
                        "maximum": 52,
                    },
                    "years_compare": {
                        "type": "integer",
                        "description": "How many calendar years ending at the latest year to include (default 5).",
                        "minimum": 2,
                        "maximum": 15,
                    },
                },
            },
        },
    },
]

# Agent 2: same national tools plus a single-state composite line (selected state).
AGENT2_OPENAI_TOOLS: list[dict[str, Any]] = [
    *AGENT3_OPENAI_TOOLS,
    {
        "type": "function",
        "function": {
            "name": "get_selected_state_composite_snapshot",
            "description": (
                "Return this app's composite risk summary for the user-selected state only (coverage, recent cases, "
                "wastewater availability, total_risk, tier). Use when comparing this state to national context."
            ),
            "parameters": {"type": "object", "properties": {}},
        },
    },
]


@dataclass
class OrchestratorRun:
    context: AgentContext
    results: dict[str, AgentResult]
    insight_quality: dict[str, InsightQCResult] = field(default_factory=dict)

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "context": self.context.to_json_dict(),
            "results": {k: v.to_json_dict() for k, v in self.results.items()},
            "insight_quality": {k: v.to_json_dict() for k, v in self.insight_quality.items()},
        }


def _insight_qc_source_bundle(ctx: AgentContext, *, max_compact_chars: int = 14000) -> str:
    """Authoritative context string for rubric scoring (matches reporters' grounding)."""
    parts = [
        _metrics_and_attribution_prefix(ctx),
        "--- Compact registry summary (tool statuses and shapes; cite counts only from context) ---",
        _compact_context_for_llm(ctx, max_chars=max_compact_chars),
    ]
    ex = ctx.extra or {}
    nt = (ex.get("national_weekly_trend_json") or "").strip()
    if nt:
        parts.append("--- national_weekly_trend_json (excerpt) ---\n" + nt[:6000])
    srj = (ex.get("state_risk_records_json") or "").strip()
    if srj:
        parts.append("--- state_risk_records_json (excerpt) ---\n" + srj[:8000])
    return "\n\n".join(parts)


def _run_insight_qc_if_enabled(
    ctx: AgentContext,
    results: dict[str, AgentResult],
) -> dict[str, InsightQCResult]:
    """Optional post-pass rubric calls (INSIGHT_QC_ENABLED). Does not mutate reporter text."""
    out: dict[str, InsightQCResult] = {}
    if not insight_qc_enabled():
        return out

    bundle = _insight_qc_source_bundle(ctx)
    r5 = results.get("agent_5")
    if r5 and r5.status == "success" and (r5.content or "").strip():
        out["national"] = run_insight_qc("national", str(r5.content), bundle)

    r4 = results.get("agent_4")
    if r4 and r4.status == "success" and (r4.content or "").strip():
        out["state"] = run_insight_qc("state", str(r4.content), bundle)

    return out


def _env_bool(name: str, default: bool = False) -> bool:
    raw = (os.getenv(name) or "").strip().lower()
    if not raw:
        return default
    return raw in ("1", "true", "yes", "on")


def _env_int(name: str, default: int, *, lo: int, hi: int) -> int:
    raw = (os.getenv(name) or "").strip()
    try:
        n = int(raw)
    except (TypeError, ValueError):
        n = default
    return max(lo, min(hi, n))


def _refinement_enabled() -> bool:
    return _env_bool("INSIGHT_REFINEMENT_ENABLED", default=False)


def _refinement_round_limits() -> tuple[int, int]:
    """
    Returns (min_rounds, max_rounds), both clamped small to cap cost/latency.
    """
    max_rounds = _env_int("INSIGHT_REFINEMENT_MAX_ROUNDS", 1, lo=1, hi=3)
    min_rounds = _env_int("INSIGHT_REFINEMENT_MIN_ROUNDS", 1, lo=1, hi=max_rounds)
    return min_rounds, max_rounds


def _refinement_user_prompt(
    *,
    role: str,
    current_text: str,
    qc: InsightQCResult,
    source_bundle: str,
    round_idx: int,
    min_rounds: int,
    max_rounds: int,
) -> str:
    label = "national summary" if role == "national" else "state summary"
    qc_json = json.dumps(qc.to_json_dict(), default=str)
    must_continue = round_idx < min_rounds
    nudge = (
        "Do not finish yet: produce a stronger revision and tighten unsupported claims."
        if must_continue
        else "If this draft already satisfies all checks, keep edits minimal and preserve grounded facts."
    )
    return (
        f"You are revising the {label} for quality and faithfulness.\n\n"
        f"Round {round_idx}/{max_rounds}. Minimum required rounds before accepting final output: {min_rounds}.\n"
        f"{nudge}\n\n"
        "Use only the Source context below; do not invent numbers.\n\n"
        "--- Source context ---\n"
        f"{source_bundle}\n\n"
        "--- Current draft ---\n"
        f"{current_text}\n\n"
        "--- QC rubric result for current draft ---\n"
        f"{qc_json}\n\n"
        "Rewrite the full draft now. Keep it concise and readable for dashboard users."
    )


def _run_refinement_if_enabled(
    ctx: AgentContext,
    results: dict[str, AgentResult],
    iq: dict[str, InsightQCResult],
) -> tuple[dict[str, AgentResult], dict[str, InsightQCResult]]:
    """
    Optional bounded rewrite loop for Agent 4/5 outputs.

    Uses Module 10-style loop controls: environment gate, min/max rounds, and a verification nudge.
    """
    if not _refinement_enabled():
        return results, iq
    if not insight_qc_enabled():
        logger.info("insight refinement skipped: INSIGHT_QC_ENABLED is off")
        return results, iq

    source_bundle = _insight_qc_source_bundle(ctx)
    min_rounds, max_rounds = _refinement_round_limits()
    role_specs = (
        ("national", "agent_5", "agent_5"),
        ("state", "agent_4", "agent_4"),
    )
    for role, key, prompt_id in role_specs:
        res = results.get(key)
        qc = iq.get(role)
        if not res or res.status != "success" or not (res.content or "").strip():
            continue
        if not qc or qc.status != "success":
            continue

        current = str(res.content)
        latest_qc = qc
        rounds_used = 0
        for round_idx in range(1, max_rounds + 1):
            rounds_used = round_idx
            if round_idx > min_rounds and latest_qc.passed is True:
                break
            revised = chat_completion(
                orchestrator_system(prompt_id),
                _refinement_user_prompt(
                    role=role,
                    current_text=current,
                    qc=latest_qc,
                    source_bundle=source_bundle,
                    round_idx=round_idx,
                    min_rounds=min_rounds,
                    max_rounds=max_rounds,
                ),
                timeout_s=90,
            )
            if not (revised or "").strip():
                msg = f"Insight refinement stopped ({role}): LLM returned no text on round {round_idx}."
                logger.warning(msg)
                res.warnings.append(msg)
                break
            current = str(revised).strip()
            latest_qc = run_insight_qc(role, current, source_bundle)
            iq[role] = latest_qc
            if latest_qc.status != "success":
                msg = f"Insight refinement halted ({role}): QC parsing failed on round {round_idx}."
                logger.warning(msg)
                res.warnings.append(msg)
                break
        res.content = current
        res.warnings.append(f"Insight refinement rounds ({role}): {rounds_used}/{max_rounds}.")

    return results, iq


def _run_tool_safe(name: str, parameters: dict[str, Any] | None) -> ToolOutput:
    try:
        return registry_run_tool(name, parameters)
    except Exception as e:
        logger.exception("Tool %s raised unexpectedly", name)
        return make_tool_output(
            name,
            "orchestrator",
            utc_as_of(),
            status="error",
            data=None,
            errors=[f"exception:{type(e).__name__}:{e}"],
            metadata={},
        )


def _merge_data_as_of(tool_outputs: dict[str, ToolOutput]) -> str:
    """Single display timestamp: lexicographic max of non-empty tool as_of strings."""
    times = [o.as_of for o in tool_outputs.values() if (o.as_of or "").strip()]
    if not times:
        return utc_as_of()
    return max(times)


def _national_analyst_user_payload(ctx: AgentContext, *, compact_chars: int = 8000) -> str:
    """
    Metrics first, then state-risk leaderboard / national trend (when present), then compact tool summary.
    Order is chosen so ``chat_completion`` truncation (keeps the start of the user message) does not drop rankings.
    """
    from risk import format_national_activity_trend_from_records_json, format_state_risk_leaderboard_from_records_json

    parts: list[str] = [_metrics_and_attribution_prefix(ctx)]
    ex = ctx.extra or {}
    raw_sr = (ex.get("state_risk_records_json") or "").strip()
    if raw_sr:
        parts.append(
            "--- STATE RISK RANKINGS (app composite; higher total_risk = more concern in this model) ---\n"
            + format_state_risk_leaderboard_from_records_json(raw_sr, limit=15)
        )
    nt = ex.get("national_weekly_trend_json")
    if nt:
        parts.append(
            "--- NATIONAL NNDSS ACTIVITY TREND (rolling / seasonal / YTD context; cite exactly) ---\n"
            + format_national_activity_trend_from_records_json(nt)
        )
    parts.append(
        "National / multi-source context (tool registry summary):\n\n"
        + _compact_context_for_llm(ctx, max_chars=compact_chars)
    )
    return "\n\n".join(parts)


def _compact_context_for_llm(ctx: AgentContext, max_chars: int = 12000) -> str:
    """Bounded text for LLM user messages (no full dataframe dumps)."""
    lines = [
        f"selected_state: {ctx.selected_state}",
        f"data_as_of: {ctx.data_as_of}",
        f"alarm_probability: {ctx.alarm_probability}",
        f"baseline_tier: {ctx.baseline_tier}",
        f"load_status: {json.dumps(ctx.load_status)}",
    ]
    for name, out in ctx.tool_outputs.items():
        chunk = {
            "tool_name": name,
            "status": out.status,
            "as_of": out.as_of,
            "errors": out.errors[:5],
        }
        if isinstance(out.data, dict):
            chunk["data_keys"] = list(out.data.keys())[:30]
            if "row_count" in out.data:
                chunk["row_count"] = out.data.get("row_count")
        lines.append(json.dumps(chunk, default=str))
    text = "\n".join(lines)
    if len(text) > max_chars:
        return text[:max_chars] + "\n... (truncated)"
    return text


def _dashboard_metrics_for_llm(ctx: AgentContext) -> str:
    """
    Fixed-format block so downstream LLM agents anchor prose to the same alarm / tier / freshness
    the UI shows. Instruct the model not to contradict or invent these values.
    """
    ap = ctx.alarm_probability
    if ap is not None:
        alarm_line = f"outbreak_alarm_probability_next_4_weeks: {float(ap):.1%}"
    else:
        alarm_line = "outbreak_alarm_probability_next_4_weeks: (not available)"
    bt = (ctx.baseline_tier or "").strip() or "(not available)"
    dao = (ctx.data_as_of or "").strip() or "(not available)"
    return (
        "--- DASHBOARD METRICS (from this app's risk model; cite exactly; do not change or invent numbers) ---\n"
        f"data_as_of: {dao}\n"
        f"{alarm_line}\n"
        f"baseline_risk_tier: {bt}\n"
        "Note: baseline_risk_tier and baseline score blend annual historical CSV with current-year NNDSS YTD "
        "(national weekly) when available—they can read elevated when YTD is high vs recent annual averages.\n"
        "Reference alarm, tier, score, and/or data freshness where relevant; do not contradict these numbers."
    )


def _risk_attribution_for_llm(ctx: AgentContext) -> str:
    """
    Baseline drivers (national historical CSV) vs state composite risk — keeps the model from
    attributing baseline to wastewater (baseline does not use WW).
    """
    ex = ctx.extra or {}
    chunks: list[str] = []
    be = (ex.get("baseline_explanation") or "").strip()
    bs = ex.get("baseline_score")
    if be or bs is not None:
        chunks.append(
            "--- BASELINE ATTRIBUTION (national Overview gauge; historical annual measles cases only — "
            "wastewater does not affect this score) ---"
        )
        if bs is not None:
            try:
                chunks.append(f"baseline_risk_score_0_to_100: {float(bs):.1f}")
            except (TypeError, ValueError):
                chunks.append(f"baseline_risk_score_0_to_100: {bs}")
        if be:
            chunks.append(be)
    srs = (ex.get("state_risk_snapshot") or "").strip()
    if srs:
        chunks.append(
            "--- STATE RISK SNAPSHOT (app composite for the selected state: coverage + recent cases + "
            "wastewater signal when available — separate from national baseline above) ---"
        )
        chunks.append(srs)
    return "\n".join(chunks) if chunks else ""


def _metrics_and_attribution_prefix(ctx: AgentContext) -> str:
    """Dashboard metrics plus optional baseline/state attribution blocks."""
    parts = [_dashboard_metrics_for_llm(ctx)]
    attr = _risk_attribution_for_llm(ctx)
    if attr:
        parts.append(attr)
    return "\n\n".join(parts)


_GEO_KEYS = (
    "Reporting Area",
    "states",
    "_state",
    "geography",
    "jurisdiction",
    "state",
    "State",
    "location1",
    "state_territory",
    "wwtp_jurisdiction",
)


def _norm_geo(s: str) -> str:
    return "".join(str(s).strip().lower().split())


def _cell_matches_state(cell: Any, selected: str) -> bool:
    if cell is None:
        return False
    raw = str(cell).strip()
    if not raw:
        return False
    u = raw.upper()
    if u in ("US RESIDENTS", "UNITED STATES", "U.S.", "US", "USA"):
        return False
    if _norm_geo(raw) == _norm_geo(selected):
        return True
    # Substring (e.g. geography text containing state name)
    if selected and len(selected) >= 3 and selected.lower() in raw.lower():
        return True
    return False


def _row_matches_state(row: dict, selected: str) -> bool:
    for key in _GEO_KEYS:
        if key in row and _cell_matches_state(row[key], selected):
            return True
    abbr = state_to_abbr(selected)
    if abbr and len(abbr) == 2:
        au = abbr.upper()
        for val in row.values():
            vs = str(val).strip().upper()
            if vs == au:
                return True
    return False


def _filter_records_for_state(records: list[dict], selected: str, max_rows: int) -> list[dict]:
    out = [r for r in records if isinstance(r, dict) and _row_matches_state(r, selected)]
    return out[:max_rows]


def _state_specific_excerpts(ctx: AgentContext, max_chars: int = 8000, per_tool_rows: int = 40) -> str:
    """
    Rows from tool payloads whose geography/reporting columns match ``ctx.selected_state``.
    Without this, the LLM only saw identical metadata per run—responses did not vary by state.
    """
    state = (ctx.selected_state or "").strip()
    if not state:
        return "(No state selected.)"
    blocks: list[str] = []
    total_tool_rows = 0
    for tool_name in TOOL_NAMES_ORDER:
        out = ctx.tool_outputs.get(tool_name)
        if out is None or not isinstance(out.data, dict):
            continue
        recs = out.data.get("records")
        if not isinstance(recs, list) or not recs:
            continue
        filtered = _filter_records_for_state(recs, state, per_tool_rows)
        total_tool_rows += len(filtered)
        if not filtered:
            continue
        payload = {
            "tool": tool_name,
            "matching_row_count": len(filtered),
            "rows": filtered,
        }
        blocks.append(json.dumps(payload, default=str))
    if total_tool_rows == 0:
        return (
            f"No rows matched **{state}** in the loaded CDC extracts (reporting column names vary by dataset, "
            "or this pull may be national-only for some sources). "
            "Say that clearly; do not invent state-specific case or coverage numbers. "
            "You may still use the DASHBOARD METRICS block in the user message for alarm and baseline tier."
        )
    text = "\n\n".join(blocks)
    if len(text) > max_chars:
        return text[:max_chars] + "\n... (truncated)"
    return text


def _agent_result(
    agent_id: str,
    status: str,
    *,
    content: str | None = None,
    error_message: str | None = None,
    warnings: list[str] | None = None,
    started_at: str | None = None,
    completed_at: str | None = None,
) -> AgentResult:
    return AgentResult(
        agent_id=agent_id,  # type: ignore[arg-type]
        status=status,  # type: ignore[arg-type]
        content=content,
        error_message=error_message,
        warnings=warnings or [],
        started_at=started_at,
        completed_at=completed_at,
    )


def _dispatch_risk_tools(ctx: AgentContext, name: str, args: dict[str, Any]) -> str:
    """Server-side handler for OpenAI tool_calls (Agents 2 and 3)."""
    if name == "get_state_risk_leaderboard":
        from risk import format_state_risk_leaderboard_from_records_json

        raw = (ctx.extra or {}).get("state_risk_records_json")
        if not raw:
            return "State risk table is not available for this run."
        lim = args.get("limit", 15)
        try:
            lim_i = int(lim)
        except (TypeError, ValueError):
            lim_i = 15
        return format_state_risk_leaderboard_from_records_json(raw, limit=lim_i)
    if name == "get_national_activity_trend":
        from risk import format_national_activity_trend_from_records_json

        raw = (ctx.extra or {}).get("national_weekly_trend_json")
        if not raw:
            return "National weekly NNDSS trend data is not available for this run."
        wc = args.get("weeks_compare", 12)
        bw = args.get("band_weeks", 8)
        yc = args.get("years_compare", 5)
        try:
            wc_i = int(wc)
        except (TypeError, ValueError):
            wc_i = 12
        try:
            bw_i = int(bw)
        except (TypeError, ValueError):
            bw_i = 8
        try:
            yc_i = int(yc)
        except (TypeError, ValueError):
            yc_i = 5
        return format_national_activity_trend_from_records_json(
            raw,
            weeks_compare=max(4, min(52, wc_i)),
            band_weeks=max(2, min(52, bw_i)),
            years_compare=max(2, min(15, yc_i)),
        )
    if name == "get_selected_state_composite_snapshot":
        from risk import format_selected_state_composite_snapshot

        return format_selected_state_composite_snapshot(ctx.extra, ctx.selected_state or "")
    return f"Unknown tool: {name}"


def _append_risk_tool_fallback_blocks(ctx: AgentContext, user_base: str) -> str:
    """Inject static leaderboard and/or national trend when not using OpenAI tool-calling (e.g. Ollama)."""
    from risk import format_national_activity_trend_from_records_json, format_state_risk_leaderboard_from_records_json

    u = user_base
    raw = (ctx.extra or {}).get("state_risk_records_json")
    if raw:
        block = format_state_risk_leaderboard_from_records_json(raw, limit=15)
        u += (
            "\n\n--- STATE RISK RANKINGS (app composite; higher total_risk = more concern in this model) ---\n"
            + block
        )
    nt = (ctx.extra or {}).get("national_weekly_trend_json")
    if nt:
        u += (
            "\n\n--- NATIONAL NNDSS ACTIVITY TREND (rolling / seasonal / YTD context; cite exactly) ---\n"
            + format_national_activity_trend_from_records_json(nt)
        )
    return u


def _llm_agent_2_state_analyst(ctx: AgentContext) -> AgentResult:
    """Tool-first pass: grounded analyst notes for the selected state."""
    t0 = _utc_now_iso()
    system = orchestrator_system("agent_2")
    excerpts = _state_specific_excerpts(ctx)
    user_base = (
        _metrics_and_attribution_prefix(ctx)
        + "\n\n"
        + f"User-selected state: **{ctx.selected_state}**\n\n"
        + "--- STATE-FILTERED DATA (CDC tool rows for this state) ---\n"
        + f"{excerpts}\n\n"
        + "--- Tool load summary (reference) ---\n"
        + f"{_compact_context_for_llm(ctx, max_chars=6000)}"
    )
    ex = ctx.extra or {}
    records = ex.get("state_risk_records_json")
    national_trend = ex.get("national_weekly_trend_json")
    use_openai_tools = bool((os.environ.get("OPENAI_API_KEY") or "").strip() and (records or national_trend))

    out: str | None = None
    if use_openai_tools:
        out = chat_completion_with_tools_openai(
            system,
            user_base,
            tools=AGENT2_OPENAI_TOOLS,
            on_tool_call=lambda n, a: _dispatch_risk_tools(ctx, n, a),
            timeout_s=90,
        )
        if out is None:
            user = _append_risk_tool_fallback_blocks(ctx, user_base)
            out = chat_completion(system, user, timeout_s=90)
    elif records or national_trend:
        user = _append_risk_tool_fallback_blocks(ctx, user_base)
        out = chat_completion(system, user, timeout_s=90)
    else:
        out = chat_completion(system, user_base, timeout_s=90)

    t1 = _utc_now_iso()
    if out is None:
        return _agent_result(
            "agent_2",
            "error",
            error_message="LLM unavailable (set OPENAI_API_KEY or OLLAMA_API_KEY; check network) or model returned no text.",
            started_at=t0,
            completed_at=t1,
        )
    return _agent_result("agent_2", "success", content=out, started_at=t0, completed_at=t1)


def _llm_agent_3_national_analyst(ctx: AgentContext) -> AgentResult:
    """Tool-first national pass: leaderboard / national trend tools + CDC tool summary."""
    t0 = _utc_now_iso()
    system = orchestrator_system("agent_3")
    # OpenAI tool path: compact prompt; model may call tools for leaderboard / trend.
    user_tools = (
        _metrics_and_attribution_prefix(ctx)
        + "\n\n"
        + "National / multi-source context (tool registry summary):\n\n"
        + _compact_context_for_llm(ctx, max_chars=8000)
    )
    # Ollama / fallback: inject ranking + trend after metrics so truncation does not strip them.
    user_with_rankings = _national_analyst_user_payload(ctx, compact_chars=8000)
    ex = ctx.extra or {}
    records = ex.get("state_risk_records_json")
    national_trend = ex.get("national_weekly_trend_json")
    use_openai_tools = bool((os.environ.get("OPENAI_API_KEY") or "").strip() and (records or national_trend))

    out: str | None = None
    if use_openai_tools:
        out = chat_completion_with_tools_openai(
            system,
            user_tools,
            tools=AGENT3_OPENAI_TOOLS,
            on_tool_call=lambda n, a: _dispatch_risk_tools(ctx, n, a),
            timeout_s=90,
        )
        if out is None:
            out = chat_completion(system, user_with_rankings, timeout_s=90)
    elif records or national_trend:
        out = chat_completion(system, user_with_rankings, timeout_s=90)
    else:
        out = chat_completion(system, user_tools, timeout_s=90)

    t1 = _utc_now_iso()
    if out is None:
        return _agent_result(
            "agent_3",
            "error",
            error_message="LLM unavailable (set OPENAI_API_KEY or OLLAMA_API_KEY; check network) or model returned no text.",
            started_at=t0,
            completed_at=t1,
        )
    return _agent_result("agent_3", "success", content=out, started_at=t0, completed_at=t1)


def _llm_agent_5_national_reporter(ctx: AgentContext, national_analyst: AgentResult) -> AgentResult:
    """Written US-wide summary from national data agent (Agent 3) output."""
    t0 = _utc_now_iso()
    system = orchestrator_system("agent_5")
    if national_analyst.status == "success" and (national_analyst.content or "").strip():
        analyst_block = national_analyst.content or ""
    else:
        err = (national_analyst.error_message or "analyst step failed").strip()
        analyst_block = (
            f"(National data agent did not complete successfully: {err}. "
            "Use DASHBOARD METRICS and tool summary below only; do not invent numbers.)"
        )
    prefix = _metrics_and_attribution_prefix(ctx) + "\n\n"
    raw_sr = (ctx.extra or {}).get("state_risk_records_json")
    ranking_section = ""
    if raw_sr and str(raw_sr).strip():
        from risk import format_state_risk_leaderboard_from_records_json, format_state_tier_counts_from_records_json

        ranking_section = (
            "--- TOP STATES BY COMPOSITE RISK (authoritative for national report sentence 5; top 3) ---\n"
            + format_state_risk_leaderboard_from_records_json(raw_sr, limit=3)
            + "\n\n--- STATES BY RISK TIER (authoritative for sentence 4 when describing distribution) ---\n"
            + format_state_tier_counts_from_records_json(raw_sr)
            + "\n\n"
        )
    # Rankings before Agent 3 prose and long tool summary so prompt truncation keeps them.
    user = (
        prefix
        + ranking_section
        + "--- NATIONAL DATA AGENT (Agent 3; authoritative for rankings and national NNDSS trend lines) ---\n"
        + analyst_block
        + "\n\n"
        + "National / multi-source context (tool registry summary):\n\n"
        + _compact_context_for_llm(ctx, max_chars=6000)
    )
    out = chat_completion(system, user, timeout_s=90)
    t1 = _utc_now_iso()
    if out is None:
        return _agent_result(
            "agent_5",
            "error",
            error_message="LLM unavailable (set OPENAI_API_KEY or OLLAMA_API_KEY; check network) or model returned no text.",
            started_at=t0,
            completed_at=t1,
        )
    return _agent_result("agent_5", "success", content=out, started_at=t0, completed_at=t1)


def _llm_agent_4_state_reporter(ctx: AgentContext, state_analyst: AgentResult) -> AgentResult:
    """State written summary from state data agent (Agent 2) tool output."""
    t0 = _utc_now_iso()
    if state_analyst.status != "success" or not (state_analyst.content or "").strip():
        return _agent_result(
            "agent_4",
            "error",
            error_message="Agent 4 skipped because the state data agent (Agent 2) did not complete successfully.",
            started_at=t0,
            completed_at=_utc_now_iso(),
        )
    system = orchestrator_system("agent_4")
    excerpts = _state_specific_excerpts(ctx, max_chars=5000, per_tool_rows=25)
    user = (
        _metrics_and_attribution_prefix(ctx)
        + "\n\n"
        + f"Selected state: **{ctx.selected_state}**\n\n"
        + "(Context: A **national US summary** already appears above this section in the app. Do not repeat US-wide story beats; focus on this state.)\n\n"
        + "--- STATE DATA AGENT (Agent 2; authoritative for tool-backed rankings and trends—do not add new facts or numbers) ---\n"
        + (state_analyst.content or "")
        + "\n\n--- STATE-FILTERED ROWS (CDC extracts for this state; consistency checks) ---\n"
        + excerpts
        + "\n\n--- Tool load summary (reference) ---\n"
        + _compact_context_for_llm(ctx, max_chars=5000)
    )
    out = chat_completion(system, user, timeout_s=90)
    t1 = _utc_now_iso()
    if out is None:
        return _agent_result(
            "agent_4",
            "error",
            error_message="LLM unavailable (set OPENAI_API_KEY or OLLAMA_API_KEY; check network) or model returned no text.",
            started_at=t0,
            completed_at=t1,
        )
    return _agent_result("agent_4", "success", content=out, started_at=t0, completed_at=t1)


def run_agent_pipeline(
    *,
    request_id: str,
    selected_state: str,
    risk_fields: RiskFields,
    tool_parameters: dict[str, dict[str, Any]] | None = None,
    run_llm_agents: bool = True,
) -> OrchestratorRun:
    """
    Run Agent 1 (tools), then optionally Agents 2–5 (LLM). Safe to call from tests or future UI code.

    Parameters
    ----------
    request_id:
        Correlates logs (e.g. Streamlit session id).
    selected_state:
        US state name for Agents 2 and 4 (e.g. "California"). Empty or whitespace means **national only**:
        run Agents 3 and 5 only (2 and 4 are stubbed empty).
    risk_fields:
        Alarm, baseline tier, and tab load_status from the existing dashboard session.
    tool_parameters:
        Optional per-tool kwargs for ``registry.run_tool`` (e.g. ``use_cache``).
    run_llm_agents:
        If False, only Agent 1 runs; Agents 2–5 are marked error with an explanatory message.
    """
    params = tool_parameters or {}
    tool_outputs: dict[str, ToolOutput] = {}
    warnings: list[str] = []

    t_agent1_start = _utc_now_iso()
    for name in TOOL_NAMES_ORDER:
        out = _run_tool_safe(name, params.get(name))
        tool_outputs[name] = out
        if out.status == "error":
            warnings.append(f"{name}: {', '.join(out.errors[:2])}")

    data_as_of = _merge_data_as_of(tool_outputs)
    any_ok = any(o.status in ("success", "partial") for o in tool_outputs.values())
    if not any_ok:
        summary = "All CDC tools failed: " + "; ".join(warnings) if warnings else "All CDC tools failed."
    else:
        n_ok = sum(1 for o in tool_outputs.values() if o.status in ("success", "partial"))
        summary = f"Loaded {n_ok}/{len(TOOL_NAMES_ORDER)} tools successfully."
        if warnings:
            summary += " Warnings: " + "; ".join(warnings)

    agent_1_status: str = "success" if any_ok else "error"
    t_agent1_end = _utc_now_iso()

    pipeline_sr_json, pipeline_state_snap = _state_risk_extras_from_tools(tool_outputs, selected_state)

    extra: dict[str, Any] = {}
    if risk_fields.baseline_explanation:
        extra["baseline_explanation"] = risk_fields.baseline_explanation
    if risk_fields.baseline_score is not None:
        extra["baseline_score"] = risk_fields.baseline_score
    state_snap = pipeline_state_snap or risk_fields.state_risk_snapshot
    if state_snap:
        extra["state_risk_snapshot"] = state_snap
    sr_json = pipeline_sr_json or risk_fields.state_risk_records_json
    if sr_json:
        extra["state_risk_records_json"] = sr_json
    if risk_fields.national_weekly_trend_json:
        extra["national_weekly_trend_json"] = risk_fields.national_weekly_trend_json

    ctx = AgentContext(
        request_id=request_id,
        selected_state=selected_state,
        data_as_of=data_as_of,
        tool_outputs=tool_outputs,
        alarm_probability=risk_fields.alarm_probability,
        baseline_tier=risk_fields.baseline_tier,
        load_status=dict(risk_fields.load_status),
        extra=extra,
    )

    results: dict[str, AgentResult] = {
        "agent_1": _agent_result(
            "agent_1",
            agent_1_status,
            content=summary,
            warnings=warnings,
            error_message=None if any_ok else "No tool returned success or partial data.",
            started_at=t_agent1_start,
            completed_at=t_agent1_end,
        )
    }

    if not run_llm_agents:
        msg = "LLM agents not run (run_llm_agents=False)."
        for aid in ("agent_2", "agent_3", "agent_4", "agent_5"):
            results[aid] = _agent_result(aid, "error", error_message=msg)
        return OrchestratorRun(context=ctx, results=results)

    state_trim = (selected_state or "").strip()
    if not state_trim:
        # National-only: Agent 3 then 5; stub empty success for state-only agents.
        t_skip = _utc_now_iso()
        r3 = _llm_agent_3_national_analyst(ctx)
        r5 = _llm_agent_5_national_reporter(ctx, r3)
        results["agent_3"] = r3
        results["agent_5"] = r5
        results["agent_2"] = _agent_result("agent_2", "success", content="", started_at=t_skip, completed_at=t_skip)
        results["agent_4"] = _agent_result("agent_4", "success", content="", started_at=t_skip, completed_at=t_skip)
        logger.info(
            "orchestrator request_id=%s national_only agent_1=%s agent_3=%s agent_5=%s",
            request_id,
            results["agent_1"].status,
            results["agent_3"].status,
            results["agent_5"].status,
        )
        iq = _run_insight_qc_if_enabled(ctx, results)
        results, iq = _run_refinement_if_enabled(ctx, results, iq)
        return OrchestratorRun(context=ctx, results=results, insight_quality=iq)

    # Agents 2 and 3 in parallel, then state reporter (4) and national reporter (5) in parallel
    with ThreadPoolExecutor(max_workers=2) as ex:
        f2 = ex.submit(_llm_agent_2_state_analyst, ctx)
        f3 = ex.submit(_llm_agent_3_national_analyst, ctx)
        r2 = f2.result()
        r3 = f3.result()
    results["agent_2"] = r2
    results["agent_3"] = r3

    with ThreadPoolExecutor(max_workers=2) as ex:
        f4 = ex.submit(_llm_agent_4_state_reporter, ctx, r2)
        f5 = ex.submit(_llm_agent_5_national_reporter, ctx, r3)
        r4 = f4.result()
        r5 = f5.result()
    results["agent_4"] = r4
    results["agent_5"] = r5

    logger.info(
        "orchestrator request_id=%s agent_1=%s agent_2=%s agent_3=%s agent_4=%s agent_5=%s",
        request_id,
        results["agent_1"].status,
        results["agent_2"].status,
        results["agent_3"].status,
        results["agent_4"].status,
        results["agent_5"].status,
    )

    iq = _run_insight_qc_if_enabled(ctx, results)
    results, iq = _run_refinement_if_enabled(ctx, results, iq)
    return OrchestratorRun(context=ctx, results=results, insight_quality=iq)
