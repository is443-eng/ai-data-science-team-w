"""
Overview tab — plain-language insights (Segment 3).

Friendly copy on Overview; technical naming lives in the instructor expander.
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone

import streamlit as st

from agents.orchestrator import RiskFields, run_agent_pipeline
from utils.state_maps import STATE_TO_ABBR


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
    if "ollama" in m or "api_key" in m:
        return (
            "We couldn’t generate the AI summaries. Add **OLLAMA_API_KEY** to your `.env` file, "
            "or turn off **Include AI-written summaries** and try again for a data-only refresh."
        )
    if "timeout" in m or "network" in m:
        return "Something timed out or the network was unavailable. Wait a moment and tap **Update my summaries** again."
    return msg


def render_agent_insights_overview() -> None:
    """Plain-language insights block on Overview (after gauge)."""
    state_options = _state_options_for_select()
    if not state_options:
        state_options = ["California"]
    default_state = state_options[0]

    if "agent_insights_state" not in st.session_state:
        st.session_state.agent_insights_state = default_state
    elif st.session_state.agent_insights_state not in state_options:
        st.session_state.agent_insights_state = default_state

    if "agent_include_llm" not in st.session_state:
        st.session_state.agent_include_llm = True

    st.divider()
    st.subheader("Plain-language insights")
    st.markdown(
        "We pull the **latest public CDC data** and turn it into **short summaries** you can read without a statistics background. "
        "This is separate from the scores and gauge above. "
        "*Not medical advice—see your clinician or "
        "[CDC measles information](https://www.cdc.gov/measles/about/index.html) for health decisions.*"
    )

    col_a, col_b = st.columns([3, 1])
    with col_a:
        st.selectbox(
            "Pick a state you care about",
            options=state_options,
            key="agent_insights_state",
            help="Most people choose their home state. One summary focuses on that state; another looks at the whole country.",
        )
    with col_b:
        st.checkbox(
            "Include AI-written summaries",
            key="agent_include_llm",
            help="When on, we add short AI paragraphs (needs an Ollama Cloud key). When off, only the automatic data check runs—usually faster.",
        )

    run_llm = bool(st.session_state.get("agent_include_llm", True))
    selected = str(st.session_state.get("agent_insights_state", default_state))

    st.caption(
        "First load can take **about 30–90 seconds** when AI summaries are on. "
        "Use the other tabs for charts and deeper technical detail."
    )

    if st.button("Update my summaries", type="primary", key="btn_agent_insights_run"):
        st.session_state.agent_last_run_error = None
        load_status = st.session_state.get("load_status") or {}
        ls = {str(k): str(v) for k, v in load_status.items()}
        rf = RiskFields(
            alarm_probability=float(st.session_state.get("alarm_prob", 0.5)),
            baseline_tier=str(st.session_state.get("baseline_tier", "low")),
            load_status=ls,
        )
        request_id = str(uuid.uuid4())
        try:
            hint = "Fetching latest CDC data and writing summaries…" if run_llm else "Fetching latest CDC data…"
            with st.spinner(hint):
                run = run_agent_pipeline(
                    request_id=request_id,
                    selected_state=selected,
                    risk_fields=rf,
                    tool_parameters=None,
                    run_llm_agents=run_llm,
                )
            st.session_state.agent_results = dict(run.results)
            st.session_state.agent_last_run_utc = datetime.now(timezone.utc).replace(microsecond=0).isoformat()
            st.session_state.agent_last_run_included_llm = run_llm
        except Exception as e:
            st.session_state.agent_results = None
            st.session_state.agent_last_run_error = str(e)
            st.session_state.agent_last_run_utc = None
            st.session_state.agent_last_run_included_llm = False

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
        st.info("Tap **Update my summaries** when you’re ready. We’ll refresh public data and, if enabled, generate readable write-ups.")
        return

    included_llm = st.session_state.get("agent_last_run_included_llm", True)

    labels = {
        "agent_1": ("Latest data check", "Automatic status of the CDC data pulls."),
        "agent_2": (f"Focus on {selected}", "Plain-language read for the state you picked."),
        "agent_3": ("National big picture", "How things look across the U.S. from the same sources."),
        "agent_4": ("Simple takeaway for families", "Short, cautious wording—not medical advice."),
    }

    r4 = results.get("agent_4")
    promoted_r4 = bool(
        included_llm
        and r4 is not None
        and r4.status == "success"
        and (r4.content or "").strip()
    )
    if promoted_r4:
        st.markdown("##### Start here")
        st.markdown(r4.content)
        st.divider()

    # Expanders: state, national, data check; optionally agent_4 if not promoted
    expander_order: list[str] = []
    if included_llm:
        expander_order.extend(["agent_2", "agent_3", "agent_1"])
        if not promoted_r4:
            expander_order.insert(0, "agent_4")
    else:
        expander_order = ["agent_1"]

    for aid in expander_order:
        res = results.get(aid)
        if res is None:
            continue
        title, subtitle = labels[aid]
        expanded = aid == "agent_1" and not included_llm
        with st.expander(title, expanded=expanded):
            st.caption(subtitle)
            if res.status == "success" and res.content:
                st.markdown(res.content)
            if res.error_message:
                disp = _friendly_pipeline_error(res.error_message) if aid != "agent_1" else res.error_message
                st.error(disp)
            for w in res.warnings or []:
                st.warning(w)

    with st.expander("How this works (for instructors and technical readers)", expanded=False):
        st.markdown(
            "**Pipeline:** **Agent 1** runs CDC-backed tools (child vaccination, kindergarten coverage, teen coverage, wastewater, NNDSS). "
            "**Agents 2–4** are optional AI summaries: state focus, national view, and family-oriented takeaway. "
            "Agent 4 is written after Agent 2 when AI is enabled."
        )
        st.markdown(
            "| Step | Role |\n"
            "|------|------|\n"
            "| Agent 1 | Data package from tool registry |\n"
            "| Agent 2 | State-focused LLM summary |\n"
            "| Agent 3 | National LLM summary |\n"
            "| Agent 4 | Family-style LLM brief |"
        )
