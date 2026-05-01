"""Registry: known tools and controlled errors for unknown names."""
from __future__ import annotations

import tools.registry as reg


def test_list_tool_names_complete():
    names = reg.list_tool_names()
    assert names == [
        "child_vax",
        "kindergarten_vax",
        "nndss",
        "teen_vax",
        "wastewater",
    ]


def test_unknown_tool_returns_error_output():
    out = reg.run_tool("not_a_real_tool", {})
    assert out.status == "error"
    assert any("unknown_tool" in e for e in out.errors)
    assert out.metadata.get("known_tools")
