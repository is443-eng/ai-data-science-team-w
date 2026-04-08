"""Contract: every ``ToolOutput`` serializes with required keys."""
from __future__ import annotations

from contracts.schemas import ToolOutput


def test_tool_output_json_shape():
    t = ToolOutput(
        tool_name="nndss",
        status="success",
        source="cdc_socrata:x9gk-5huc",
        as_of="2026-01-01 00:00",
        data={"columns": [], "records": [], "row_count": 0},
        errors=[],
        metadata={"view_id": "x9gk-5huc"},
    )
    d = t.to_json_dict()
    assert set(d.keys()) >= {"tool_name", "status", "source", "as_of", "data", "errors", "metadata"}
    assert d["tool_name"] == "nndss"
    assert d["status"] == "success"
