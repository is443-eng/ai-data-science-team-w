"""Shared helpers for tool wrappers: retries, timestamps, DataFrame JSON payloads."""
from __future__ import annotations

import json
import time
from typing import Any, Callable, TypeVar

import pandas as pd
import requests

from contracts.schemas import ToolOutput, ToolStatus

T = TypeVar("T")


def utc_as_of() -> str:
    return time.strftime("%Y-%m-%d %H:%M", time.gmtime())


def dataframe_to_json_payload(df: pd.DataFrame) -> dict[str, Any]:
    """JSON-serializable table payload (records + column names)."""
    if df is None or df.empty:
        return {"columns": [], "records": [], "row_count": 0}
    records = json.loads(df.to_json(orient="records", date_format="iso"))
    return {"columns": list(df.columns), "records": records, "row_count": len(records)}


def loader_status_to_tool_status(load_status: str, df: pd.DataFrame, errors: list[str]) -> ToolStatus:
    if load_status == "fail":
        return "error"
    if errors:
        return "partial"
    return "success"


def make_tool_output(
    tool_name: str,
    source: str,
    as_of: str,
    *,
    status: ToolStatus,
    data: dict[str, Any] | list[Any] | None,
    errors: list[str],
    metadata: dict[str, Any],
) -> ToolOutput:
    return ToolOutput(
        tool_name=tool_name,
        status=status,
        source=source,
        as_of=as_of,
        data=data,
        errors=errors,
        metadata=metadata,
    )


def retry_http(
    fn: Callable[[], T],
    *,
    retries: int = 3,
    base_delay_s: float = 0.75,
    retry_on: tuple[type, ...] = (requests.RequestException, requests.Timeout),
) -> T:
    """Run ``fn`` with retries on transient HTTP failures."""
    last: Exception | None = None
    for attempt in range(retries):
        try:
            return fn()
        except retry_on as e:
            last = e
            if attempt == retries - 1:
                raise
            time.sleep(base_delay_s * (2**attempt))
    raise last  # pragma: no cover


def retry_call(
    fn: Callable[[], T],
    *,
    retries: int = 3,
    base_delay_s: float = 0.5,
    retry_when: Callable[[T], bool],
) -> T:
    """Retry when ``retry_when(result)`` is True."""
    last = None
    for attempt in range(retries):
        result = fn()
        if not retry_when(result):
            return result
        last = result
        if attempt < retries - 1:
            time.sleep(base_delay_s * (2**attempt))
    return last  # type: ignore
