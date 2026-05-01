"""Wastewater measles signal tool — wraps ``loaders.load_wastewater`` (V1-compatible)."""
from __future__ import annotations

from typing import Any

from loaders import load_wastewater
from tools._common import dataframe_to_json_payload, loader_status_to_tool_status, make_tool_output, utc_as_of

TOOL_NAME = "wastewater"
SOURCE = "cdc_socrata:akvg-8vrb"


def run(parameters: dict[str, Any] | None = None) -> ToolOutput:
    parameters = parameters or {}
    use_cache = bool(parameters.get("use_cache", True))
    as_of = utc_as_of()
    errors: list[str] = []
    try:
        df, load_status = load_wastewater(use_cache=use_cache)
    except Exception as e:
        return make_tool_output(
            TOOL_NAME,
            SOURCE,
            as_of,
            status="error",
            data=None,
            errors=[f"wastewater_load_exception:{e}"],
            metadata={"view_id": "akvg-8vrb", "parameters": {"use_cache": use_cache}},
        )
    if load_status == "fail":
        errors.append("wastewater_fetch_failed_check_token_or_network")
    status = loader_status_to_tool_status(load_status, df, errors)
    data = dataframe_to_json_payload(df)
    return make_tool_output(
        TOOL_NAME,
        SOURCE,
        as_of,
        status=status,
        data=data,
        errors=errors,
        metadata={"view_id": "akvg-8vrb", "v1_load_status": load_status, "parameters": {"use_cache": use_cache}},
    )
