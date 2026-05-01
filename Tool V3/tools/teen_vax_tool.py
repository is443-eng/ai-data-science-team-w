"""Teen (13–17) MMR coverage tool — CDC ``ee48-w5t6`` (V1 script–compatible defaults)."""
from __future__ import annotations

from typing import Any, Optional

import pandas as pd

from tools._common import dataframe_to_json_payload, make_tool_output, retry_http, utc_as_of
from tools.cdc_child_teen import (
    TEEN_DEFAULT_WHERE,
    TEEN_VIEW_ID,
    _get_token,
    clean_teen_vax_data,
    soda3_select,
)

TOOL_NAME = "teen_vax"
SOURCE = "cdc_socrata:ee48-w5t6"


def run(parameters: dict[str, Any] | None = None) -> ToolOutput:
    parameters = parameters or {}
    limit = int(parameters.get("limit", 50_000))
    timeout = int(parameters.get("timeout_s", 90))
    if "where" in parameters:
        w = parameters["where"]
        where: Optional[str] = None if w is None or str(w).strip() == "" else str(w)
    else:
        where = TEEN_DEFAULT_WHERE

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
            metadata={"view_id": TEEN_VIEW_ID, "parameters": {k: parameters.get(k) for k in ("limit", "where", "timeout_s")}},
        )

    def fetch() -> list:
        return soda3_select(token, TEEN_VIEW_ID, where, limit=limit, timeout=timeout)

    try:
        raw = retry_http(fetch, retries=int(parameters.get("retries", 3)))
    except Exception as e:
        return make_tool_output(
            TOOL_NAME,
            SOURCE,
            as_of,
            status="error",
            data=None,
            errors=[f"teen_vax_http:{e}"],
            metadata={"view_id": TEEN_VIEW_ID, "retryable": True},
        )

    df = pd.DataFrame(raw)
    raw_count = len(df)
    df = clean_teen_vax_data(df)
    data = dataframe_to_json_payload(df)
    meta = {
        "view_id": TEEN_VIEW_ID,
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
