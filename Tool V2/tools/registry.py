"""
Tool registry for dynamic invocation (orchestrator / agents).

Registered names are stable API surface for Segment 2+.
"""
from __future__ import annotations

from typing import Any, Callable

from contracts.schemas import ToolOutput

from tools._common import make_tool_output, utc_as_of
from tools.child_vax_tool import run as run_child_vax
from tools.kindergarten_vax_tool import run as run_kindergarten_vax
from tools.nndss_tool import run as run_nndss
from tools.teen_vax_tool import run as run_teen_vax
from tools.wastewater_tool import run as run_wastewater

ToolRunner = Callable[[dict[str, Any] | None], ToolOutput]

REGISTERED_TOOLS: dict[str, ToolRunner] = {
    "child_vax": run_child_vax,
    "kindergarten_vax": run_kindergarten_vax,
    "teen_vax": run_teen_vax,
    "wastewater": run_wastewater,
    "nndss": run_nndss,
}


def list_tool_names() -> list[str]:
    return sorted(REGISTERED_TOOLS.keys())


def run_tool(tool_name: str, parameters: dict[str, Any] | None = None) -> ToolOutput:
    """
    Execute a tool by name. Unknown names return ``ToolOutput`` with
    ``status=\"error\"`` and a controlled error message (no exception).
    """
    if tool_name not in REGISTERED_TOOLS:
        return make_tool_output(
            tool_name,
            "registry",
            utc_as_of(),
            status="error",
            data=None,
            errors=[f"unknown_tool:{tool_name}", f"known_tools:{','.join(list_tool_names())}"],
            metadata={"known_tools": list_tool_names()},
        )
    return REGISTERED_TOOLS[tool_name](parameters)
