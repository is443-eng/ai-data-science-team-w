"""
Overview tab — plain-language insights (Segment 3).

Friendly copy on Overview; technical naming lives in the instructor expander.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

import pandas as pd
import streamlit as st

from agents.orchestrator import RiskFields, run_agent_pipeline
from risk import format_state_risk_snapshot_line, get_baseline_risk_components
from utils.state_maps import STATE_TO_ABBR


def _risk_fields_from_session(selected_state: str) -> RiskFields:
    load_status = st.session_state.get("load_status") or {}
    ls = {str(k): str(v) for k, v in load_status.items()}
    hist = st.session_state.get("hist")
    nndss = st.session_state.get("nndss")
    if hist is None:
        hist = pd.DataFrame()
    if nndss is None:
        nndss = pd.DataFrame()
    comp = get_baseline_risk_components(hist, nndss, state_risk_df=st.session_state.get("state_risk_df"))
    lines: list[str] = []
    if comp.get("recent_5yr_avg") is not None:
        lines.append(f"recent_5yr_avg_annual_cases: {comp['recent_5yr_avg']}")
    if comp.get("overall_avg") is not None:
        lines.append(f"overall_avg_annual_cases: {comp['overall_avg']}")
    if comp.get("ratio") is not None:
        lines.append(f"recent_to_overall_ratio: {comp['ratio']}")
    if comp.get("formula"):
        lines.append(f"formula: {comp['formula']}")
    if (comp.get("interpretation_note") or "").strip():
        lines.append(str(comp["interpretation_note"]).strip())
    if (comp.get("harmonization_note") or "").strip():
        lines.append(str(comp["harmonization_note"]).strip())
    baseline_explanation = "\n".join(lines) if lines else None
    bv = st.session_state.get("baseline_val")
    if bv is None:
        bs = float(comp["score"]) if comp.get("score") is not None else None
    else:
        try:
            bs = float(bv)
        except (TypeError, ValueError):
            bs = float(comp["score"]) if comp.get("score") is not None else None
    state_snap = format_state_risk_snapshot_line(st.session_state.get("state_risk_df"), selected_state)
    sr = st.session_state.get("state_risk_df")
    sr_json: str | None = None
    if sr is not None and not sr.empty:
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
        if cols:
            sr_json = sr[cols].to_json(orient="records")
    nndss_agg = st.session_state.get("nndss_agg")
    national_weekly_trend_json = None
    if nndss_agg is not None and not getattr(nndss_agg, "empty", True):
        from risk import national_weekly_trend_json_from_agg

        national_weekly_trend_json = national_weekly_trend_json_from_agg(nndss_agg)
    return RiskFields(
        alarm_probability=float(st.session_state.get("alarm_prob", 0.5)),
        baseline_tier=str(comp.get("tier") or st.session_state.get("baseline_tier") or "low"),
        baseline_score=bs,
        baseline_explanation=baseline_explanation,
        state_risk_snapshot=state_snap,
        state_risk_records_json=sr_json,
        national_weekly_trend_json=national_weekly_trend_json,
        load_status=ls,
    )


def _state_options_for_select() -> list[str]:
    sr = st.session_state.get("state_risk_df")
    if sr is not None and not sr.empty and "state" in sr.columns:
        return sorted(sr["state"].astype(str).unique().tolist())
    return sorted(STATE_TO_ABBR.keys())


def _format_last_run_utc(iso_ts: str) -> str:
    """Readable UTC time."""
    try:
        raw = iso_ts.replace("Z", "+00:00")
        dt = datetime.fromisoformat(raw)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)
        return dt.strftime("%b %d, %Y · %I:%M %p UTC")
    except (ValueError, TypeError):
        return iso_ts


def _friendly_pipeline_error(msg: str) -> str:
    m = (msg or "").lower()
    if "ollama" in m or "openai" in m or "api_key" in m:
        return (
            "We couldn’t generate the AI summaries. Add **OPENAI_API_KEY** (OpenAI) or **OLLAMA_API_KEY** (Ollama Cloud) "
            "to your environment or `.env`, or set them on Posit Connect under **Vars**. "
            "You can turn off **Include AI-written summaries** for a data-only refresh."
        )
    if "timeout" in m or "network" in m:
        return "Something timed out or the network was unavailable. Wait a moment and tap **Generate insights** again."
    return msg


NATIONAL_ONLY_LABEL = "— National only —"


def _qc_field(res: Any, name: str, default: Any = None) -> Any:
    if res is None:
        return default
    if isinstance(res, dict):
        return res.get(name, default)
    return getattr(res, name, default)


def _render_insight_quality_expander() -> None:
    """Show optional Module 09–style rubric when INSIGHT_QC_ENABLED produced results."""
    iq = st.session_state.get("agent_insight_quality") or {}
    if not iq:
        return
    with st.expander("Insight quality rubric (optional)", expanded=False):
        st.caption(
            "Enabled when **INSIGHT_QC_ENABLED=1**. A separate model pass scores each summary against the same CDC "
            "context. Adjust **INSIGHT_QC_MIN_OVERALL** (default 3.0) and **INSIGHT_QC_REQUIRE_ACCURATE** (default on)."
        )
        for title, key in (("National summary", "national"), ("State summary", "state")):
            r = iq.get(key)
            if not r:
                continue
            st.markdown(f"**{title}**")
            status = _qc_field(r, "status")
            if status == "skipped":
                st.caption("Skipped (no text).")
                continue
            if status == "error":
                st.warning(_qc_field(r, "error_message") or "QC failed.")
                continue
            passed = _qc_field(r, "passed")
            overall = _qc_field(r, "overall_score")
            acc = _qc_field(r, "accurate")
            det = _qc_field(r, "details")
            if passed is True:
                st.success(f"Pass — overall {overall}/5 (accurate={acc}).")
            elif passed is False:
                st.error(f"Below threshold — overall {overall}/5 (accurate={acc}).")
            else:
                st.info(f"Scored — overall {overall}/5 (accurate={acc}).")
            if det:
                st.caption(det)


def _render_agent_result(res: Any, *, friendly_llm_errors: bool = True) -> None:
    """Streamlit: show one AgentResult."""
    if res is None:
        return
    if res.status == "success" and (res.content or "").strip():
        st.markdown(res.content)
    if res.error_message:
        disp = _friendly_pipeline_error(res.error_message) if friendly_llm_errors else res.error_message
        st.error(disp)
    for w in res.warnings or []:
        st.warning(w)


def render_agent_insights_overview() -> None:
    """Insights block on Overview: optional state, Generate insights, national-only or full pipeline."""
    base_opts = _state_options_for_select()
    state_options = [NATIONAL_ONLY_LABEL] + base_opts

    if "agent_insights_state" not in st.session_state:
        st.session_state.agent_insights_state = NATIONAL_ONLY_LABEL
    elif st.session_state.agent_insights_state not in state_options:
        st.session_state.agent_insights_state = NATIONAL_ONLY_LABEL

    if "agent_include_llm" not in st.session_state:
        st.session_state.agent_include_llm = True

    st.divider()
    st.subheader("Insights")
    st.markdown(
        "Refresh CDC-backed data and generate readable summaries. "
        "*Not medical advice—see [CDC measles information](https://www.cdc.gov/measles/about/index.html) for health decisions.*"
    )

    col_a, col_b = st.columns([3, 1])
    with col_a:
        st.selectbox(
            "State (optional)",
            options=state_options,
            key="agent_insights_state",
            help="**National only** shows a US-wide summary. Choose a state to add a short state summary below the national summary.",
        )
    with col_b:
        st.checkbox(
            "Include AI-written summaries",
            key="agent_include_llm",
            help="When on, we call the LLM (needs OPENAI_API_KEY or OLLAMA_API_KEY). When off, only the automatic CDC data check runs—usually faster.",
        )

    run_llm = bool(st.session_state.get("agent_include_llm", True))
    raw_pick = st.session_state.agent_insights_state
    selected_state = "" if raw_pick == NATIONAL_ONLY_LABEL else str(raw_pick).strip()
    run_display_state = raw_pick if raw_pick != NATIONAL_ONLY_LABEL else ""

    st.caption(
        "First run can take **about 30–90 seconds** when AI summaries are on (CDC fetch + model). "
        "**Generate insights** refreshes CDC tool data and runs the selected analysis."
    )

    if st.button("Generate insights", type="primary", key="btn_agent_insights_run"):
        st.session_state.agent_last_run_error = None
        rf = _risk_fields_from_session(selected_state)
        request_id = str(uuid.uuid4())
        try:
            hint = "Fetching CDC data and generating insights…" if run_llm else "Fetching CDC data…"
            with st.spinner(hint):
                run = run_agent_pipeline(
                    request_id=request_id,
                    selected_state=selected_state,
                    risk_fields=rf,
                    tool_parameters=None,
                    run_llm_agents=run_llm,
                )
            st.session_state.agent_results = dict(run.results)
            st.session_state.agent_insight_quality = dict(run.insight_quality)
            st.session_state.agent_last_run_utc = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
            st.session_state.agent_last_run_included_llm = run_llm
            st.session_state.agent_last_run_had_state = bool(selected_state.strip())
            st.session_state.agent_last_run_display_state = run_display_state or None
        except Exception as e:
            st.session_state.agent_results = None
            st.session_state.agent_insight_quality = {}
            st.session_state.agent_last_run_error = str(e)
            st.session_state.agent_last_run_utc = None
            st.session_state.agent_last_run_included_llm = False
            st.session_state.agent_last_run_had_state = False
            st.session_state.agent_last_run_display_state = None

    err = st.session_state.get("agent_last_run_error")
    if err:
        st.error(_friendly_pipeline_error(err))
        with st.expander("Technical details", expanded=False):
            st.code(str(err))

    ts = st.session_state.get("agent_last_run_utc")
    if ts:
        st.caption(f"Last updated: {_format_last_run_utc(ts)}")

    results = st.session_state.get("agent_results")
    if not results:
        st.info("Tap **Generate insights** when you’re ready. We refresh public CDC data and, if enabled, generate the summaries above.")
        return

    included_llm = st.session_state.get("agent_last_run_included_llm", True)

    if not included_llm:
        r1 = results.get("agent_1")
        with st.expander("Latest data check", expanded=True):
            st.caption("Automatic status of the CDC data pulls.")
            _render_agent_result(r1, friendly_llm_errors=False)
        return

    had_state = bool(st.session_state.get("agent_last_run_had_state", False))
    state_label = st.session_state.get("agent_last_run_display_state") or "Your state"

    r5 = results.get("agent_5")
    r4 = results.get("agent_4")
    r1 = results.get("agent_1")

    if not had_state:
        st.subheader("National summary")
        _render_agent_result(r5)
        _render_insight_quality_expander()
        with st.expander("How this run works", expanded=False):
            st.markdown(
                "**National only:** Agent 1 loads CDC tools; **Agent 3** (national data analyst) and **Agent 5** "
                "(national reporter) produce the US-wide summary. State-level agents are not run. Pick a state and run again "
                "to add a state summary."
            )
        return

    st.subheader("National summary")
    _render_agent_result(r5)

    st.subheader(f"{state_label}: state summary")
    st.caption("Readable summary from the state data agent—not medical advice.")
    _render_agent_result(r4)

    _render_insight_quality_expander()

    st.subheader("Latest data check")
    st.caption("Automatic status of the CDC data pulls.")
    _render_agent_result(r1, friendly_llm_errors=False)

    with st.expander("How this works (for instructors and technical readers)", expanded=False):
        st.markdown(
            "**Pipeline:** **Agent 1** runs CDC-backed tools. **Agent 3** (national data analyst) and **Agent 5** (national reporter) "
            "produce the US-wide summary. With a state selected, **Agent 2** runs in parallel with **Agent 3**, then **Agent 4** "
            "(state reporter) runs in parallel with **Agent 5**. **Display order** on this page: national summary → state summary → data check."
        )
        st.markdown(
            "| Step | Role |\n"
            "|------|------|\n"
            "| Agent 1 | Tool registry: load CDC extracts |\n"
            "| Agent 2 | State data analyst (OpenAI tools + CDC rows) |\n"
            "| Agent 3 | National data analyst (tools + registry summary) |\n"
            "| Agent 4 | State reporter (from Agent 2 + excerpts) |\n"
            "| Agent 5 | National reporter (from Agent 3 + metrics) |"
        )
