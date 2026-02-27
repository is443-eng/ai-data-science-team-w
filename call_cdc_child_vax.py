#!/usr/bin/env python3
"""
Call the CDC Socrata API: Vaccination Coverage among Young Children 0-35 Months (fhky-rtsk).
By default fetches only vaccine_name = '≥1 Dose MMR'. Uses SOCRATA_APP_TOKEN from .env.

Dataset: https://dev.socrata.com/foundry/data.cdc.gov/fhky-rtsk

Usage:
  python call_cdc_child_vax.py                    # MMR ≥1 dose only
  python call_cdc_child_vax.py --where ""        # all vaccines, no filter
  python call_cdc_child_vax.py --where "year=2023" --limit 500
  python call_cdc_child_vax.py --schema
  python call_cdc_child_vax.py --out data/raw/child_vax.csv
  python call_cdc_child_vax.py --unique vaccine_name
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

PROJECT_ROOT = Path(__file__).resolve().parent
try:
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env")
except ImportError:
    pass

VIEW_ID = "fhky-rtsk"
META_URL = f"https://data.cdc.gov/api/views/{VIEW_ID}.json"
LEGACY_URL = f"https://data.cdc.gov/resource/{VIEW_ID}.json"
SODA3_URL = f"https://data.cdc.gov/api/v3/views/{VIEW_ID}/query.json"

# Default: only ≥1 Dose MMR (exact name from API). Use --where "" for all vaccines.
# We use SODA3 (POST) by default so this Unicode value goes in the JSON body, not the URL.
DEFAULT_WHERE = 'vaccine_name = "≥1 Dose MMR"'


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


def call_legacy(token: str, limit: int, where: Optional[str], select: str = "*") -> list:
    params = {"$select": select, "$limit": str(limit)}
    if where:
        params["$where"] = where
    r = requests.get(LEGACY_URL, headers={"X-App-Token": token}, params=params, timeout=60)
    r.raise_for_status()
    return r.json()


def call_soda3(token: str, limit: int, where: Optional[str], select: str = "*") -> list:
    soql = f"SELECT {select}" + (f" WHERE {where}" if where else "")
    payload = {"query": soql, "page": {"pageNumber": 1, "pageSize": limit}}
    r = requests.post(SODA3_URL, headers={"X-App-Token": token, "Content-Type": "application/json"}, json=payload, timeout=60)
    r.raise_for_status()
    data = r.json()
    return data.get("data", data) if isinstance(data, dict) else (data if isinstance(data, list) else [])


def main():
    parser = argparse.ArgumentParser(description="CDC Socrata API: Vaccination Coverage Young Children 0-35 mo (fhky-rtsk)")
    parser.add_argument("--legacy", action="store_true", help="Use legacy GET (default is SODA3 POST; needed for default filter with Unicode)")
    parser.add_argument("--limit", type=int, default=1000, help="Max rows (default 1000)")
    parser.add_argument("--where", type=str, default=None, help="SoQL WHERE clause (default: vaccine_name = '≥1 Dose MMR'); use '' for no filter")
    parser.add_argument("--out", type=str, help="Save DataFrame to this file as CSV")
    parser.add_argument("--table", action="store_true", help="Print full data as a table in the terminal")
    parser.add_argument("--quiet", action="store_true", help="Only print record count and column headers")
    parser.add_argument("--schema", action="store_true", help="Print column list and exit")
    parser.add_argument("--unique", type=str, metavar="COLUMN", help="Print every distinct value for COLUMN (use --schema to see column names)")
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
    # Default: MMR ≥1 dose only; --where "" means no filter
    where = DEFAULT_WHERE if args.where is None else (args.where.strip() or None)
    select = "*"

    if args.unique:
        col = args.unique.strip()
        select = col
        limit = 50000  # fetch more rows to capture all distinct values
        data = call_legacy(token, limit, where, select=select) if args.legacy else call_soda3(token, limit, where, select=select)
        df = pd.DataFrame(data)
        if col not in df.columns:
            print(f"Column '{col}' not found. Use --schema to list columns.", file=sys.stderr)
            print(f"Available: {', '.join(df.columns)}", file=sys.stderr)
            sys.exit(1)
        uniq = sorted(df[col].dropna().astype(str).unique())
        print(f"Unique values for '{col}' ({len(uniq)}):")
        for v in uniq:
            print(f"  {v}")
        return

    data = call_legacy(token, args.limit, where) if args.legacy else call_soda3(token, args.limit, where)
    df = pd.DataFrame(data)
    print(f"Records returned: {len(df)}")
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
