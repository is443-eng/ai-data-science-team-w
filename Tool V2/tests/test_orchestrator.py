"""Orchestrator: Agent 1 tools, Agents 2–4 LLM order and partial failure (mocked)."""
from __future__ import annotations

import os
from unittest.mock import MagicMock, patch

from contracts.schemas import AgentContext, ToolOutput
from tools._common import make_tool_output, utc_as_of


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
        if "state-filtered rows" in system:
            order.append("agent_2")
            return "state text"
        if "national-level" in system:
            order.append("agent_3")
            return "national text"
        if "concerned parent" in system:
            order.append("agent_4")
            return "parent text"
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

    assert "agent_2" in order and "agent_3" in order
    assert order.index("agent_4") > max(order.index("agent_2"), order.index("agent_3"))


@patch("ollama_client._load_env")
@patch("agents.orchestrator.registry_run_tool")
def test_missing_api_key_llm_agents_error(mock_tools: MagicMock, mock_load_env: MagicMock, monkeypatch) -> None:
    """chat_completion returns None when OLLAMA_API_KEY is unset (conftest may load .env)."""
    mock_tools.side_effect = lambda name, p=None: _ok_tool(name)
    from agents.orchestrator import RiskFields, run_agent_pipeline

    mock_load_env.return_value = None
    monkeypatch.delenv("OLLAMA_API_KEY", raising=False)
    run = run_agent_pipeline(
        request_id="t4",
        selected_state="Texas",
        risk_fields=RiskFields(),
        run_llm_agents=True,
    )

    assert run.results["agent_2"].status == "error"
    assert run.results["agent_3"].status == "error"
    assert run.results["agent_4"].status == "error"


@patch("agents.orchestrator.chat_completion")
@patch("agents.orchestrator.registry_run_tool")
def test_agent4_skipped_when_agent2_fails(mock_tools: MagicMock, mock_chat: MagicMock) -> None:
    mock_tools.side_effect = lambda name, p=None: _ok_tool(name)

    def chat_side(system: str, user: str, *, timeout_s: int = 90) -> str | None:
        if "state-filtered rows" in system:
            return None
        if "national-level" in system:
            return "ok"
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
