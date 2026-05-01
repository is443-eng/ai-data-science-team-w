"""Orchestrator: Agent 1 tools, Agents 2–5 LLM order and partial failure (mocked)."""
from __future__ import annotations

import json
import os
from unittest.mock import MagicMock, patch

from contracts.schemas import AgentContext, ToolOutput

from tools._common import make_tool_output, utc_as_of


def test_metrics_and_attribution_prefix_includes_baseline_and_state_blocks() -> None:
    from agents.orchestrator import _metrics_and_attribution_prefix

    ctx = AgentContext(
        request_id="r",
        selected_state="Ohio",
        data_as_of="d",
        extra={
            "baseline_explanation": "recent_5yr_avg_annual_cases: 10",
            "baseline_score": 42.0,
            "state_risk_snapshot": "total_risk_0_to_100: 55",
        },
    )
    text = _metrics_and_attribution_prefix(ctx)
    assert "DASHBOARD METRICS" in text
    assert "BASELINE ATTRIBUTION" in text
    assert "STATE RISK SNAPSHOT" in text
    assert "42.0" in text
    assert "total_risk_0_to_100" in text


def _ok_tool(name: str) -> ToolOutput:
    return make_tool_output(
        name,
        "test",
        utc_as_of(),
        status="success",
        data={"row_count": 1},
        errors=[],
        metadata={},
    )


def _err_tool(name: str) -> ToolOutput:
    return make_tool_output(
        name,
        "test",
        utc_as_of(),
        status="error",
        data=None,
        errors=["fail"],
        metadata={},
    )


def test_row_matches_state_reporting_area() -> None:
    from agents.orchestrator import _row_matches_state

    assert _row_matches_state({"Reporting Area": "OHIO"}, "Ohio")
    assert _row_matches_state({"Reporting Area": "California"}, "California")
    assert not _row_matches_state({"Reporting Area": "US RESIDENTS"}, "Ohio")
    assert not _row_matches_state({"Reporting Area": "Texas"}, "Ohio")


def test_state_risk_extras_from_tools_populates_leaderboard_json_from_nndss() -> None:
    """Agent 1 payloads (not session) must supply state_risk_records_json for national reporter TOP STATES."""
    from agents.orchestrator import _state_risk_extras_from_tools

    rows_nndss = []
    for week in (13, 12, 11, 10):
        rows_nndss.append({"Reporting Area": "California", "year": 2026, "week": week, "m1": 25.0})
        rows_nndss.append({"Reporting Area": "Texas", "year": 2026, "week": week, "m1": 10.0})
    data_n = {"columns": ["Reporting Area", "year", "week", "m1"], "records": rows_nndss, "row_count": len(rows_nndss)}
    nndss_out = ToolOutput(
        tool_name="nndss",
        status="success",
        source="t",
        as_of="x",
        data=data_n,
        errors=[],
        metadata={},
    )
    tool_outputs = {
        "child_vax": _ok_tool("child_vax"),
        "kindergarten_vax": _ok_tool("kindergarten_vax"),
        "teen_vax": _ok_tool("teen_vax"),
        "wastewater": _ok_tool("wastewater"),
        "nndss": nndss_out,
    }
    js, snap = _state_risk_extras_from_tools(tool_outputs, "California")
    assert js is not None
    import json

    arr = json.loads(js)
    assert len(arr) >= 4
    assert any(r.get("state") == "California" for r in arr)
    assert snap is not None and "coverage_pct" in snap


def test_state_specific_excerpts_includes_only_matching_state() -> None:
    from agents.orchestrator import _state_specific_excerpts

    records = [
        {"Reporting Area": "OHIO", "m1": 1},
        {"Reporting Area": "TEXAS", "m1": 2},
    ]
    data = {"columns": ["Reporting Area", "m1"], "records": records, "row_count": 2}
    oh = ToolOutput(
        tool_name="nndss",
        status="success",
        source="t",
        as_of="x",
        data=data,
        errors=[],
        metadata={},
    )
    ctx = AgentContext(
        request_id="r",
        selected_state="Ohio",
        data_as_of="d",
        tool_outputs={"nndss": oh},
    )
    text = _state_specific_excerpts(ctx, max_chars=10000)
    assert "OHIO" in text or "Ohio" in text
    assert "TEXAS" not in text


@patch("agents.orchestrator.registry_run_tool")
def test_agent1_runs_all_tools(mock_run: MagicMock) -> None:
    mock_run.side_effect = lambda name, p=None: _ok_tool(name)
    from agents.orchestrator import RiskFields, run_agent_pipeline

    run = run_agent_pipeline(
        request_id="t1",
        selected_state="Ohio",
        risk_fields=RiskFields(alarm_probability=0.1, baseline_tier="low", load_status={"historical": "ok"}),
        run_llm_agents=False,
    )
    assert mock_run.call_count == 5
    names = [c[0][0] for c in mock_run.call_args_list]
    assert names == ["child_vax", "kindergarten_vax", "teen_vax", "wastewater", "nndss"]
    assert run.results["agent_1"].status == "success"
    assert "5/5" in (run.results["agent_1"].content or "")


@patch("agents.orchestrator.chat_completion")
@patch("agents.orchestrator.registry_run_tool")
def test_national_only_runs_agent3_llm_only(mock_tools: MagicMock, mock_chat: MagicMock) -> None:
    """Empty selected_state: Agent 3 then Agent 5; state agents stubbed empty."""
    mock_tools.side_effect = lambda name, p=None: _ok_tool(name)
    mock_chat.side_effect = ["national analyst draft", "national report final"]
    from agents.orchestrator import RiskFields, run_agent_pipeline

    old = os.environ.pop("OLLAMA_API_KEY", None)
    try:
        os.environ["OLLAMA_API_KEY"] = "test-key"
        run = run_agent_pipeline(
            request_id="t_nat",
            selected_state="",
            risk_fields=RiskFields(),
            run_llm_agents=True,
        )
    finally:
        if old is not None:
            os.environ["OLLAMA_API_KEY"] = old
        else:
            os.environ.pop("OLLAMA_API_KEY", None)

    assert mock_chat.call_count == 2
    assert run.results["agent_3"].status == "success"
    assert (run.results["agent_3"].content or "") == "national analyst draft"
    assert run.results["agent_5"].status == "success"
    assert (run.results["agent_5"].content or "") == "national report final"
    assert run.results["agent_2"].status == "success"
    assert not (run.results["agent_2"].content or "").strip()
    assert run.results["agent_4"].status == "success"
    assert not (run.results["agent_4"].content or "").strip()


@patch("agents.orchestrator.registry_run_tool")
def test_partial_tool_failure(mock_run: MagicMock) -> None:
    def side(name: str, p=None) -> ToolOutput:
        if name == "nndss":
            return _err_tool(name)
        return _ok_tool(name)

    mock_run.side_effect = side
    from agents.orchestrator import RiskFields, run_agent_pipeline

    run = run_agent_pipeline(
        request_id="t2",
        selected_state="Ohio",
        risk_fields=RiskFields(),
        run_llm_agents=False,
    )
    assert run.results["agent_1"].status == "success"
    assert run.results["agent_1"].warnings
    assert "nndss" in run.results["agent_1"].warnings[0]


@patch("agents.orchestrator.chat_completion")
@patch("agents.orchestrator.registry_run_tool")
def test_order_parallel_then_sequential(mock_tools: MagicMock, mock_chat: MagicMock) -> None:
    mock_tools.side_effect = lambda name, p=None: _ok_tool(name)
    order: list[str] = []

    def chat_side(system: str, user: str, *, timeout_s: int = 90) -> str | None:
        s = system or ""
        if "Tool-first" in s and "national data analyst" in s:
            order.append("agent_3")
            return "national analyst"
        if "National **reporter**" in s:
            order.append("agent_5")
            return "national text"
        if "Tool-first" in s and "state data analyst" in s:
            order.append("agent_2")
            return "analyst text"
        if "State **reporter**" in s:
            order.append("agent_4")
            return "state text"
        order.append("unknown")
        return "x"

    mock_chat.side_effect = chat_side
    from agents.orchestrator import RiskFields, run_agent_pipeline

    old = os.environ.pop("OLLAMA_API_KEY", None)
    try:
        os.environ["OLLAMA_API_KEY"] = "test-key"
        run_agent_pipeline(
            request_id="t3",
            selected_state="Texas",
            risk_fields=RiskFields(),
            run_llm_agents=True,
        )
    finally:
        if old is not None:
            os.environ["OLLAMA_API_KEY"] = old
        else:
            os.environ.pop("OLLAMA_API_KEY", None)

    assert "agent_2" in order and "agent_3" in order and "agent_4" in order and "agent_5" in order
    i2, i3 = order.index("agent_2"), order.index("agent_3")
    i4, i5 = order.index("agent_4"), order.index("agent_5")
    assert max(i2, i3) < min(i4, i5)


@patch("ollama_client._load_env")
@patch("agents.orchestrator.registry_run_tool")
def test_missing_api_key_llm_agents_error(mock_tools: MagicMock, mock_load_env: MagicMock, monkeypatch) -> None:
    """chat_completion returns None when no LLM key is set (conftest may load .env)."""
    mock_tools.side_effect = lambda name, p=None: _ok_tool(name)
    from agents.orchestrator import RiskFields, run_agent_pipeline

    mock_load_env.return_value = None
    monkeypatch.delenv("OLLAMA_API_KEY", raising=False)
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    run = run_agent_pipeline(
        request_id="t4",
        selected_state="Texas",
        risk_fields=RiskFields(),
        run_llm_agents=True,
    )

    assert run.results["agent_2"].status == "error"
    assert run.results["agent_3"].status == "error"
    assert run.results["agent_4"].status == "error"
    assert run.results["agent_5"].status == "error"


@patch("agents.orchestrator.chat_completion")
@patch("agents.orchestrator.registry_run_tool")
def test_agent4_skipped_when_agent2_fails(mock_tools: MagicMock, mock_chat: MagicMock) -> None:
    mock_tools.side_effect = lambda name, p=None: _ok_tool(name)

    def chat_side(system: str, user: str, *, timeout_s: int = 90) -> str | None:
        s = system or ""
        if "Tool-first" in s and "national data analyst" in s:
            return "nat analyst ok"
        if "National **reporter**" in s:
            return "nat report ok"
        if "Tool-first" in s and "state data analyst" in s:
            return None
        if "State **reporter**" in s:
            return "should not reach"
        return "should not reach"

    mock_chat.side_effect = chat_side
    from agents.orchestrator import RiskFields, run_agent_pipeline

    old = os.environ.pop("OLLAMA_API_KEY", None)
    try:
        os.environ["OLLAMA_API_KEY"] = "k"
        run = run_agent_pipeline(
            request_id="t5",
            selected_state="Florida",
            risk_fields=RiskFields(),
            run_llm_agents=True,
        )
    finally:
        if old is not None:
            os.environ["OLLAMA_API_KEY"] = old
        else:
            os.environ.pop("OLLAMA_API_KEY", None)

    assert run.results["agent_2"].status == "error"
    assert run.results["agent_4"].status == "error"
    assert "skipped" in (run.results["agent_4"].error_message or "").lower()


@patch("agents.orchestrator.registry_run_tool")
def test_all_tools_fail_agent1_error(mock_run: MagicMock) -> None:
    mock_run.side_effect = lambda name, p=None: _err_tool(name)
    from agents.orchestrator import RiskFields, run_agent_pipeline

    run = run_agent_pipeline(
        request_id="t6",
        selected_state="X",
        risk_fields=RiskFields(),
        run_llm_agents=False,
    )
    assert run.results["agent_1"].status == "error"


@patch("agents.orchestrator.chat_completion")
@patch("agents.orchestrator.registry_run_tool")
def test_agent4_receives_state_analyst_from_agent2(mock_tools: MagicMock, mock_chat: MagicMock) -> None:
    """Agent 4 user message must include Agent 2 (state data agent) output."""
    mock_tools.side_effect = lambda name, p=None: _ok_tool(name)

    def chat_side(system: str, user: str, *, timeout_s: int = 90) -> str | None:
        s = system or ""
        if "Tool-first" in s and "national data analyst" in s:
            return "NAT_ANALYST"
        if "National **reporter**" in s:
            return "nat report"
        if "Tool-first" in s and "state data analyst" in s:
            return "STATE_DATA_AGENT_2_OUTPUT"
        if "State **reporter**" in s:
            assert "STATE_DATA_AGENT_2_OUTPUT" in user
            return "state reporter ok"
        return "z"

    mock_chat.side_effect = chat_side
    from agents.orchestrator import RiskFields, run_agent_pipeline

    old = os.environ.pop("OLLAMA_API_KEY", None)
    try:
        os.environ["OLLAMA_API_KEY"] = "k"
        run = run_agent_pipeline(
            request_id="t_a24",
            selected_state="Texas",
            risk_fields=RiskFields(),
            run_llm_agents=True,
        )
    finally:
        if old is not None:
            os.environ["OLLAMA_API_KEY"] = old
        else:
            os.environ.pop("OLLAMA_API_KEY", None)

    assert run.results["agent_4"].status == "success"
    assert (run.results["agent_2"].content or "") == "STATE_DATA_AGENT_2_OUTPUT"


def test_dispatch_risk_tools_national_activity_trend() -> None:
    from agents.orchestrator import _dispatch_risk_tools

    rows = [{"year": 2024, "week": w, "cases": 1.0} for w in range(1, 30)]
    ctx = AgentContext(
        request_id="r",
        selected_state="",
        data_as_of="d",
        extra={"national_weekly_trend_json": json.dumps(rows)},
    )
    out = _dispatch_risk_tools(ctx, "get_national_activity_trend", {})
    assert "National NNDSS" in out


def test_run_agent_pipeline_extra_includes_national_weekly_trend_json() -> None:
    from agents.orchestrator import RiskFields, run_agent_pipeline

    run = run_agent_pipeline(
        request_id="t7",
        selected_state="",
        risk_fields=RiskFields(national_weekly_trend_json='[{"year":2024,"week":1,"cases":1}]'),
        run_llm_agents=False,
    )
    assert run.context.extra.get("national_weekly_trend_json") is not None
