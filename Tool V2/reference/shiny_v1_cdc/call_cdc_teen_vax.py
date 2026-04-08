#!/usr/bin/env python3
"""
Call the CDC Socrata API: Vaccination Coverage among Adolescents 13-17 Years (ee48-w5t6).
Uses SOCRATA_APP_TOKEN from .env. Supports legacy GET and SODA3 POST.
By default fetches MMR-only (≥2 Doses MMR). Fetched data is cleaned every run.

Dataset: https://dev.socrata.com/foundry/data.cdc.gov/ee48-w5t6

Usage:
  python call_cdc_teen_vax.py
  python call_cdc_teen_vax.py --where "year=2023" --limit 500
  python call_cdc_teen_vax.py --schema
  python call_cdc_teen_vax.py --out data/raw/teen_vax.csv
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

_SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = _SCRIPT_DIR.parent
try:
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env")
    load_dotenv(_SCRIPT_DIR / ".env")
except ImportError:
    pass

VIEW_ID = "ee48-w5t6"
META_URL = f"https://data.cdc.gov/api/views/{VIEW_ID}.json"

# Default: MMR only (teen dataset has ≥2 Doses MMR for MMR)
DEFAULT_WHERE = 'vaccine = "≥2 Doses MMR"'
MMR_VACCINE_VALUES = {"≥2 Doses MMR"}
# Keep only national or state-level; exclude HHS regions
GEOGRAPHY_TYPE_STATES = "States/Local Areas"
GEOGRAPHY_NATIONAL = "United States"
LEGACY_URL = f"https://data.cdc.gov/resource/{VIEW_ID}.json"
SODA3_URL = f"https://data.cdc.gov/api/v3/views/{VIEW_ID}/query.json"


def clean_teen_vax_data(df: pd.DataFrame) -> pd.DataFrame:
    """
    Filter to (1) MMR vaccine rows only, (2) national or state-level geography (exclude HHS regions).
    """
    if df.empty:
        return df
    if "vaccine" not in df.columns:
        print("Warning: 'vaccine' column not found; skipping clean. Columns:", list(df.columns), file=sys.stderr)
        return df
    df = df.loc[df["vaccine"].astype(str).str.strip().isin(MMR_VACCINE_VALUES)].copy()
    # National or state-level only (no HHS regions)
    if "geography_type" in df.columns and "geography" in df.columns:
        state_level = df["geography_type"].astype(str).str.strip() == GEOGRAPHY_TYPE_STATES
        national = df["geography"].astype(str).str.strip() == GEOGRAPHY_NATIONAL
        df = df.loc[state_level | national].copy()
    return df


def get_token() -> str:
    token = os.environ.get("SOCRATA_APP_TOKEN", "").strip()
    if not token:
        print("Error: SOCRATA_APP_TOKEN not set. Add it to .env in the project root.", file=sys.stderr)
        sys.exit(1)
    return token


def fetch_schema() -> list:
    r = requests.get(META_URL, timeout=30)
    r.raise_for_status()
    return r.json().get("columns", [])


def call_legacy(token: str, limit: int, where: Optional[str]) -> list:
    params = {"$select": "*", "$limit": str(limit)}
    if where:
        params["$where"] = where
    r = requests.get(LEGACY_URL, headers={"X-App-Token": token}, params=params, timeout=60)
    r.raise_for_status()
    return r.json()


def call_soda3(token: str, limit: int, where: Optional[str]) -> list:
    soql = "SELECT *" + (f" WHERE {where}" if where else "")
    payload = {"query": soql, "page": {"pageNumber": 1, "pageSize": limit}}
    r = requests.post(SODA3_URL, headers={"X-App-Token": token, "Content-Type": "application/json"}, json=payload, timeout=60)
    r.raise_for_status()
    data = r.json()
    return data.get("data", data) if isinstance(data, dict) else (data if isinstance(data, list) else [])


def main():
    parser = argparse.ArgumentParser(description="CDC Socrata API: Vaccination Coverage Adolescents 13-17 (ee48-w5t6)")
    parser.add_argument("--soda3", action="store_true", help="Use SODA3 POST instead of legacy GET")
    parser.add_argument("--limit", type=int, default=50000, help="Max rows per request (default 50000; Socrata max per request)")
    parser.add_argument("--where", type=str, default=None, help="SoQL WHERE clause (default: MMR only); use '' for no filter")
    parser.add_argument("--out", type=str, help="Save DataFrame to this file as CSV")
    parser.add_argument("--table", action="store_true", help="Print full data as a table in the terminal")
    parser.add_argument("--quiet", action="store_true", help="Only print record count and column headers")
    parser.add_argument("--schema", action="store_true", help="Print column list and exit")
    args = parser.parse_args()

    if args.schema:
        try:
            for col in fetch_schema():
                print(f"  {col.get('fieldName', '')}  [{col.get('dataTypeName', '')}]  — {col.get('name', '')}")
        except Exception as e:
            print(f"Could not fetch schema: {e}", file=sys.stderr)
            sys.exit(1)
        return

    token = get_token()
    where = DEFAULT_WHERE if args.where is None else (args.where.strip() or None)
    data = call_soda3(token, args.limit, where) if args.soda3 else call_legacy(token, args.limit, where)

    df = pd.DataFrame(data)
    raw_count = len(df)
    df = clean_teen_vax_data(df)
    print(f"Records returned (raw): {raw_count}, after cleaning: {len(df)}")
    if len(df) > 0:
        print(f"Columns: {', '.join(df.columns)}")
    if args.out:
        df.to_csv(args.out, index=False)
        print(f"Saved to {args.out} (CSV)")
    if args.table and len(df) > 0:
        pd.set_option("display.max_rows", None)
        pd.set_option("display.max_columns", None)
        pd.set_option("display.width", None)
        pd.set_option("display.max_colwidth", 50)
        print("\nFull data:")
        print(df.to_string())
    elif not args.quiet and len(df) > 0:
        print("\nFirst row:")
        print(df.head(1).to_string())


if __name__ == "__main__":
    main()
