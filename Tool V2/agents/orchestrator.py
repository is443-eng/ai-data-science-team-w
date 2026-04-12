"""
Central orchestrator for Agents 1–4 (Segment 2).

Execution order: Agent 1 (CDC tools via registry) → Agents 2 & 3 in parallel (LLM) → Agent 4 (LLM, after Agent 2).

This module is **additive**: the Streamlit app can import it when Phase B wires the UI. It does not alter loaders or existing tabs by itself.

Partial failure: tool or LLM errors become AgentResult.error with messages; other agents still run when possible.
Agent 4 is skipped with a clear error if Agent 2 did not succeed (no parent brief without state analysis).
"""
from __future__ import annotations

import json
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any

from contracts.schemas import AgentContext, AgentResult, ToolOutput

from ollama_client import chat_completion
from prompts.loader import orchestrator_system
from tools._common import make_tool_output, utc_as_of
from tools.registry import run_tool as registry_run_tool
from utils.logging_config import get_logger
from utils.state_maps import state_to_abbr

logger = get_logger("orchestrator")

# Must match Segment 1 registry; fixed order for reproducible tests and logs.
TOOL_NAMES_ORDER = ("child_vax", "kindergarten_vax", "teen_vax", "wastewater", "nndss")


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@dataclass
class RiskFields:
    """Risk/session fields supplied by the app (orchestrator does not recompute model outputs)."""

    alarm_probability: float | None = None
    baseline_tier: str | None = None
    load_status: dict[str, str] = field(default_factory=dict)


@dataclass
class OrchestratorRun:
    context: AgentContext
    results: dict[str, AgentResult]

    def to_json_dict(self) -> dict[str, Any]:
        return {
            "context": self.context.to_json_dict(),
            "results": {k: v.to_json_dict() for k, v in self.results.items()},
        }


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


_GEO_KEYS = (
    "Reporting Area",
    "states",
    "_state",
    "geography",
    "jurisdiction",
    "state",
    "State",
    "location1",
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
            "Say that clearly; do not invent state-specific case or coverage numbers."
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


def _llm_agent_2_state(ctx: AgentContext) -> AgentResult:
    t0 = _utc_now_iso()
    system = orchestrator_system("agent_2")
    excerpts = _state_specific_excerpts(ctx)
    user = (
        f"User-selected state: **{ctx.selected_state}**\n\n"
        "--- STATE-FILTERED DATA (use this; it changes when the state changes) ---\n"
        f"{excerpts}\n\n"
        "--- Tool load summary (reference; mostly identical across states) ---\n"
        f"{_compact_context_for_llm(ctx, max_chars=6000)}"
    )
    out = chat_completion(system, user, timeout_s=90)
    t1 = _utc_now_iso()
    if out is None:
        return _agent_result(
            "agent_2",
            "error",
            error_message="LLM unavailable (check OLLAMA_API_KEY and network) or model returned no text.",
            started_at=t0,
            completed_at=t1,
        )
    return _agent_result("agent_2", "success", content=out, started_at=t0, completed_at=t1)


def _llm_agent_3_national(ctx: AgentContext) -> AgentResult:
    t0 = _utc_now_iso()
    system = orchestrator_system("agent_3")
    user = "National / multi-source summary:\n\n" + _compact_context_for_llm(ctx)
    out = chat_completion(system, user, timeout_s=90)
    t1 = _utc_now_iso()
    if out is None:
        return _agent_result(
            "agent_3",
            "error",
            error_message="LLM unavailable (check OLLAMA_API_KEY and network) or model returned no text.",
            started_at=t0,
            completed_at=t1,
        )
    return _agent_result("agent_3", "success", content=out, started_at=t0, completed_at=t1)


def _llm_agent_4_parent(ctx: AgentContext, agent_2: AgentResult) -> AgentResult:
    t0 = _utc_now_iso()
    if agent_2.status != "success" or not (agent_2.content or "").strip():
        return _agent_result(
            "agent_4",
            "error",
            error_message="Agent 4 skipped because Agent 2 did not complete successfully (parent brief requires state analysis).",
            started_at=t0,
            completed_at=_utc_now_iso(),
        )
    system = orchestrator_system("agent_4")
    excerpts = _state_specific_excerpts(ctx, max_chars=5000, per_tool_rows=25)
    user = (
        f"Selected state: **{ctx.selected_state}**\n\n"
        "State-level analysis (from prior step):\n"
        + (agent_2.content or "")
        + "\n\nState-filtered rows (same as Agent 2 used):\n"
        + excerpts
        + "\n\nTool load summary (reference):\n"
        + _compact_context_for_llm(ctx, max_chars=5000)
    )
    out = chat_completion(system, user, timeout_s=90)
    t1 = _utc_now_iso()
    if out is None:
        return _agent_result(
            "agent_4",
            "error",
            error_message="LLM unavailable (check OLLAMA_API_KEY and network) or model returned no text.",
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
    Run Agent 1 (tools), then optionally Agents 2–4 (LLM). Safe to call from tests or future UI code.

    Parameters
    ----------
    request_id:
        Correlates logs (e.g. Streamlit session id).
    selected_state:
        US state name for Agent 2 framing (e.g. "California").
    risk_fields:
        Alarm, baseline tier, and tab load_status from the existing dashboard session.
    tool_parameters:
        Optional per-tool kwargs for ``registry.run_tool`` (e.g. ``use_cache``).
    run_llm_agents:
        If False, only Agent 1 runs; Agents 2–4 are marked error with an explanatory message.
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

    ctx = AgentContext(
        request_id=request_id,
        selected_state=selected_state,
        data_as_of=data_as_of,
        tool_outputs=tool_outputs,
        alarm_probability=risk_fields.alarm_probability,
        baseline_tier=risk_fields.baseline_tier,
        load_status=dict(risk_fields.load_status),
        extra={},
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
        for aid in ("agent_2", "agent_3", "agent_4"):
            results[aid] = _agent_result(aid, "error", error_message=msg)
        return OrchestratorRun(context=ctx, results=results)

    # Agents 2 and 3 in parallel
    with ThreadPoolExecutor(max_workers=2) as ex:
        f2 = ex.submit(_llm_agent_2_state, ctx)
        f3 = ex.submit(_llm_agent_3_national, ctx)
        r2 = f2.result()
        r3 = f3.result()
    results["agent_2"] = r2
    results["agent_3"] = r3

    results["agent_4"] = _llm_agent_4_parent(ctx, r2)

    logger.info(
        "orchestrator request_id=%s agent_1=%s agent_2=%s agent_3=%s agent_4=%s",
        request_id,
        results["agent_1"].status,
        results["agent_2"].status,
        results["agent_3"].status,
        results["agent_4"].status,
    )

    return OrchestratorRun(context=ctx, results=results)
