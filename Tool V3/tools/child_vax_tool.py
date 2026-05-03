"""Child (0–35 mo) MMR coverage tool — CDC ``fhky-rtsk`` (V1 script–compatible defaults)."""
from __future__ import annotations

from typing import Any, Optional

import pandas as pd

from tools._common import dataframe_to_json_payload, make_tool_output, retry_http, utc_as_of
from tools.cdc_child_teen import (
    CHILD_DEFAULT_WHERE,
    CHILD_VIEW_ID,
    _get_token,
    clean_child_vax_data,
    soda3_select,
)

TOOL_NAME = "child_vax"
SOURCE = "cdc_socrata:fhky-rtsk"


def run(parameters: dict[str, Any] | None = None) -> ToolOutput:
    parameters = parameters or {}
    use_cache = bool(parameters.get("use_cache", True))
    limit = int(parameters.get("limit", 50_000))
    timeout = int(parameters.get("timeout_s", 90))
    where: Optional[str]
    if "where" in parameters:
        w = parameters["where"]
        where = None if w is None or str(w).strip() == "" else str(w)
    else:
        where = CHILD_DEFAULT_WHERE

    as_of = utc_as_of()
    token = _get_token()
    if not token:
        return make_tool_output(
            TOOL_NAME,
            SOURCE,
            as_of,
            status="error",
            data=None,
            errors=["SOCRATA_APP_TOKEN not set"],
            metadata={
                "view_id": CHILD_VIEW_ID,
                "parameters": {k: parameters.get(k) for k in ("limit", "where", "timeout_s", "use_cache")},
            },
        )

    def fetch() -> list:
        return soda3_select(token, CHILD_VIEW_ID, where, limit=limit, timeout=timeout, use_cache=use_cache)

    try:
        raw = retry_http(fetch, retries=int(parameters.get("retries", 3)))
    except Exception as e:
        return make_tool_output(
            TOOL_NAME,
            SOURCE,
            as_of,
            status="error",
            data=None,
            errors=[f"child_vax_http:{e}"],
            metadata={"view_id": CHILD_VIEW_ID, "retryable": True},
        )

    df = pd.DataFrame(raw)
    raw_count = len(df)
    df = clean_child_vax_data(df)
    data = dataframe_to_json_payload(df)
    meta = {
        "view_id": CHILD_VIEW_ID,
        "raw_row_count_before_clean": raw_count,
        "clean_row_count": data.get("row_count", 0),
        "where": where,
        "parameters": {"limit": limit, "timeout_s": timeout},
    }
    return make_tool_output(
        TOOL_NAME,
        SOURCE,
        as_of,
        status="success",
        data=data,
        errors=[],
        metadata=meta,
    )
