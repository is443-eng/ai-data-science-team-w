"""
Shared payload contracts for App V3 tool layer, orchestration, and UI.

These types are the single source of truth for JSON shapes passed between
tools, the orchestrator, and Streamlit. Implementations should serialize
with the same field names (snake_case).
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal, Optional

ToolStatus = Literal["success", "partial", "error"]
AgentId = Literal["agent_1", "agent_2", "agent_3", "agent_4", "agent_5"]
AgentRunStatus = Literal["pending", "running", "success", "error"]


@dataclass
class ToolInput:
    """Invocation of a single data tool (one API domain)."""

    tool_name: str
    parameters: dict[str, Any] = field(default_factory=dict)
    """Tool-specific args; must remain backward-compatible with V1 dashboard semantics."""


@dataclass
class ToolOutput:
    """Normalized result from any tool wrapper."""

    tool_name: str
    status: ToolStatus
    source: str
    as_of: str
    data: Optional[dict[str, Any] | list[Any]] = None
    errors: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_json_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class AgentContext:
    """Shared context published after Agent 1; consumed by downstream LLM agents and the UI."""

    request_id: str
    selected_state: str
    data_as_of: str
    tool_outputs: dict[str, ToolOutput] = field(default_factory=dict)
    alarm_probability: Optional[float] = None
    baseline_tier: Optional[str] = None
    load_status: dict[str, str] = field(default_factory=dict)
    extra: dict[str, Any] = field(default_factory=dict)

    def to_json_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["tool_outputs"] = {k: v.to_json_dict() if isinstance(v, ToolOutput) else v for k, v in self.tool_outputs.items()}
        return d


@dataclass
class AgentResult:
    """One agent card payload for the Overview tab."""

    agent_id: AgentId
    status: AgentRunStatus
    content: Optional[str | dict[str, Any]] = None
    error_message: Optional[str] = None
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    warnings: list[str] = field(default_factory=list)

    def to_json_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class ToolErrorDetail:
    """Standard error envelope for orchestration (timeouts, HTTP, validation)."""

    code: str
    message: str
    retryable: bool = False
    detail: Optional[dict[str, Any]] = None

    def to_json_dict(self) -> dict[str, Any]:
        return asdict(self)
