#!/usr/bin/env python3
"""
Call the CDC Socrata NNDSS API (dataset x9gk-5huc). By default fetches rows for
Measles, Indigenous and Measles, Imported (all columns). Supports legacy GET and SODA3 POST.
Fetched data is automatically cleaned to national (US RESIDENTS) and state-level (Location1 populated) rows only.

Dataset: https://dev.socrata.com/foundry/data.cdc.gov/x9gk-5huc

Usage:
  From project root:  venv/bin/python call_cdc_nndss.py
  No filter:          venv/bin/python call_cdc_nndss.py --where ""
  Custom filter:      venv/bin/python call_cdc_nndss.py --where "year=2019"
  Print columns:      venv/bin/python call_cdc_nndss.py --schema
  Save as CSV:        venv/bin/python call_cdc_nndss.py --out data/raw/nndss_measles.csv
"""

import argparse
import os
import sys
from pathlib import Path
from typing import Optional

try:
    import requests
except ImportError:
    print("Install requests: pip install requests", file=sys.stderr)
    sys.exit(1)
try:
    import pandas as pd
except ImportError:
    print("Install pandas: pip install pandas", file=sys.stderr)
    sys.exit(1)

# .env from project root (parent of Shiny App V1) or current dir
_SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = _SCRIPT_DIR.parent
try:
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env")
    load_dotenv(_SCRIPT_DIR / ".env")
except ImportError:
    pass

# Dataset: x9gk-5huc (see https://dev.socrata.com/foundry/data.cdc.gov/x9gk-5huc)
VIEW_ID = "x9gk-5huc"
META_URL = f"https://data.cdc.gov/api/views/{VIEW_ID}.json"
LEGACY_URL = f"https://data.cdc.gov/resource/{VIEW_ID}.json"
SODA3_URL = f"https://data.cdc.gov/api/v3/views/{VIEW_ID}/query.json"


def get_token():
    token = os.environ.get("SOCRATA_APP_TOKEN", "").strip()
    if not token:
        print("Error: SOCRATA_APP_TOKEN not set. Add it to .env in the project root.", file=sys.stderr)
        sys.exit(1)
    return token


# Labels we want: Measles, Indigenous and Measles, Imported only
ALLOWED_LABELS = {"Measles, Indigenous", "Measles, Imported"}

# Reporting Area value for national statistics
NATIONAL_REPORTING_AREA = "US RESIDENTS"


def clean_nndss_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter NNDSS data to:
    - Label in {"Measles, Indigenous", "Measles, Imported"}
    - National stats (Reporting Area = "US RESIDENTS") OR state-level (Location1 populated)
    """
    if df.empty:
        return df

    # Reporting Area: API may use "Reporting Area" or "states" (SoQL fieldName)
    reporting_area_col = "Reporting Area" if "Reporting Area" in df.columns else "states"
    required_cols = ["label", reporting_area_col, "location1"]
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        print(f"Warning: columns {missing} not found; skipping clean. Columns: {list(df.columns)}", file=sys.stderr)
        return df

    # Filter to allowed labels only
    label_mask = df["label"].astype(str).str.strip().isin(ALLOWED_LABELS)

    # National (Reporting Area = "US RESIDENTS") or state-level (location1 populated)
    states_national = df[reporting_area_col].astype(str).str.strip() == NATIONAL_REPORTING_AREA
    location1_populated = df["location1"].notna() & (df["location1"].astype(str).str.strip() != "")
    geo_mask = states_national | location1_populated

    return df.loc[label_mask & geo_mask].copy()


def fetch_schema() -> list:
    """Fetch view metadata and return column definitions (fieldName, name, dataTypeName)."""
    r = requests.get(META_URL, timeout=30)
    r.raise_for_status()
    meta = r.json()
    return meta.get("columns", [])


# Default: only Measles, Indigenous and Measles, Imported
DEFAULT_WHERE = "label in ('Measles, Indigenous', 'Measles, Imported')"


def call_legacy(token: str, limit: int, where: Optional[str]) -> list:
    """Legacy SODA 2.1: GET with $query params. All columns (*)."""
    params = {"$select": "*", "$limit": str(limit)}
    if where:
        params["$where"] = where
    headers = {"X-App-Token": token}
    r = requests.get(LEGACY_URL, headers=headers, params=params, timeout=60)
    r.raise_for_status()
    return r.json()


def call_soda3(token: str, limit: int, where: Optional[str]) -> list:
    """SODA3: POST with JSON body. All columns (*)."""
    soql = "SELECT *"
    if where:
        soql += f" WHERE {where}"
    payload = {
        "query": soql,
        "page": {"pageNumber": 1, "pageSize": limit},
    }
    headers = {
        "X-App-Token": token,
        "Content-Type": "application/json",
    }
    r = requests.post(SODA3_URL, headers=headers, json=payload, timeout=60)
    r.raise_for_status()
    data = r.json()
    if isinstance(data, dict) and "data" in data:
        return data["data"]
    if isinstance(data, list):
        return data
    return []


def main():
    parser = argparse.ArgumentParser(description="Call CDC Socrata API - dataset x9gk-5huc (all columns, optional filter)")
    parser.add_argument("--soda3", action="store_true", help="Use SODA3 POST endpoint instead of legacy GET")
    parser.add_argument("--limit", type=int, default=50000, help="Max rows per request (default 50000; Socrata max per request)")
    parser.add_argument("--where", type=str, default=None, help="SoQL WHERE clause (default: Measles Indigenous/Imported only); use '' for no filter")
    parser.add_argument("--out", type=str, help="Save DataFrame to this file as CSV")
    parser.add_argument("--quiet", action="store_true", help="Only print record count and column headers")
    parser.add_argument("--schema", action="store_true", help="Print column list from dataset metadata and exit")
    args = parser.parse_args()

    if args.schema:
        try:
            columns = fetch_schema()
            print("Columns (fieldName = SoQL name):")
            for col in columns:
                name = col.get("fieldName", "")
                label = col.get("name", name)
                dtype = col.get("dataTypeName", "")
                print(f"  {name}  [{dtype}]  — {label}")
        except Exception as e:
            print(f"Could not fetch schema: {e}", file=sys.stderr)
            sys.exit(1)
        return

    token = get_token()

    # Default: Measles Indigenous/Imported only; --where "" means no filter
    where = DEFAULT_WHERE if args.where is None else (args.where.strip() or None)
    if args.soda3:
        data = call_soda3(token, limit=args.limit, where=where)
    else:
        data = call_legacy(token, limit=args.limit, where=where)

    df = pd.DataFrame(data)
    raw_count = len(df)
    df = clean_nndss_data(df)
    print(f"Records returned (raw): {raw_count}, after cleaning: {len(df)}")

    if len(df) > 0:
        print(f"Column headers in data ({len(df.columns)}): {', '.join(df.columns)}")

    if args.out:
        df.to_csv(args.out, index=False)
        print(f"Saved to {args.out} (CSV)")

    if not args.quiet and len(df) > 0:
        print("\nFirst row:")
        print(df.head(1).to_string())
        if len(df) > 1:
            print("\n... (use --out to save full DataFrame as CSV)")


if __name__ == "__main__":
    main()
