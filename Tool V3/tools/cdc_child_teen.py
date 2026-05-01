"""
CDC Socrata child (0–35 mo) and teen (13–17) MMR coverage fetches.
Aligned with ``reference/shiny_v1_cdc/call_cdc_child_vax.py`` and ``call_cdc_teen_vax.py``.
"""
from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Optional

import pandas as pd
import requests

from utils.logging_config import get_logger

logger = get_logger("tools.cdc_child_teen")

TOOL_V2_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = TOOL_V2_DIR.parent

CHILD_VIEW_ID = "fhky-rtsk"
TEEN_VIEW_ID = "ee48-w5t6"

CHILD_DEFAULT_WHERE = 'vaccine = "≥1 Dose MMR"'
TEEN_DEFAULT_WHERE = 'vaccine = "≥2 Doses MMR"'

CHILD_MMR = {"≥1 Dose MMR"}
TEEN_MMR = {"≥2 Doses MMR"}

GEOGRAPHY_TYPE_STATES = "States/Local Areas"
GEOGRAPHY_NATIONAL = "United States"


def _get_token() -> Optional[str]:
    try:
        from dotenv import load_dotenv

        load_dotenv(PROJECT_ROOT / ".env")
        load_dotenv(TOOL_V2_DIR / ".env")
    except ImportError:
        pass
    return (os.environ.get("SOCRATA_APP_TOKEN") or "").strip() or None


def clean_child_vax_data(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    if "vaccine" not in df.columns:
        logger.warning("child vax: no vaccine column")
        return df
    df = df.loc[df["vaccine"].astype(str).str.strip().isin(CHILD_MMR)].copy()
    if "geography_type" in df.columns and "geography" in df.columns:
        state_level = df["geography_type"].astype(str).str.strip() == GEOGRAPHY_TYPE_STATES
        national = df["geography"].astype(str).str.strip() == GEOGRAPHY_NATIONAL
        df = df.loc[state_level | national].copy()
    return df


def clean_teen_vax_data(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df
    if "vaccine" not in df.columns:
        logger.warning("teen vax: no vaccine column")
        return df
    df = df.loc[df["vaccine"].astype(str).str.strip().isin(TEEN_MMR)].copy()
    if "geography_type" in df.columns and "geography" in df.columns:
        state_level = df["geography_type"].astype(str).str.strip() == GEOGRAPHY_TYPE_STATES
        national = df["geography"].astype(str).str.strip() == GEOGRAPHY_NATIONAL
        df = df.loc[state_level | national].copy()
    return df


def soda3_select(
    token: str,
    view_id: str,
    where: Optional[str],
    *,
    limit: int,
    timeout: int,
) -> list[dict[str, Any]]:
    url = f"https://data.cdc.gov/api/v3/views/{view_id}/query.json"
    soql = "SELECT *" + (f" WHERE {where}" if where else "")
    payload = {"query": soql, "page": {"pageNumber": 1, "pageSize": limit}}
    headers = {"X-App-Token": token, "Content-Type": "application/json"}
    r = requests.post(url, headers=headers, json=payload, timeout=timeout)
    r.raise_for_status()
    data = r.json()
    if isinstance(data, dict) and "data" in data:
        return data["data"]
    if isinstance(data, list):
        return data
    return []
