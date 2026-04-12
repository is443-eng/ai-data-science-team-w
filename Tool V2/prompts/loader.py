"""Load markdown system prompts for the orchestrator (Phase C)."""
from __future__ import annotations

from pathlib import Path

_PROMPTS_DIR = Path(__file__).resolve().parent

_ROLE_FILES = {
    "agent_2": "agent_2_state.md",
    "agent_3": "agent_3_national.md",
    "agent_4": "agent_4_parent.md",
}


def _read(name: str) -> str:
    path = _PROMPTS_DIR / name
    return path.read_text(encoding="utf-8").strip()


def orchestrator_system(role: str) -> str:
    """
    Combined system prompt: shared guardrails + role-specific instructions.
    ``role`` is ``agent_2``, ``agent_3``, or ``agent_4``.
    """
    if role not in _ROLE_FILES:
        raise ValueError(f"Unknown orchestrator role: {role!r}")
    guard = _read("shared_guardrails.md")
    body = _read(_ROLE_FILES[role])
    return f"{guard}\n\n{body}"
