#!/usr/bin/env python3
"""
Call the CDC Socrata API: Vaccination Coverage among Young Children 0-35 Months (fhky-rtsk).
Uses SOCRATA_APP_TOKEN from .env. Supports legacy GET and SODA3 POST.

Dataset: https://dev.socrata.com/foundry/data.cdc.gov/fhky-rtsk

Usage:
  python call_cdc_child_vax.py
  python call_cdc_child_vax.py --where "year=2023" --limit 500
  python call_cdc_child_vax.py --schema
  python call_cdc_child_vax.py --out child_vax.json
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Optional

try:
    import requests
except ImportError:
    print("Install requests: pip install requests", file=sys.stderr)
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
    parser = argparse.ArgumentParser(description="CDC Socrata API: Vaccination Coverage Young Children 0-35 mo (fhky-rtsk)")
    parser.add_argument("--soda3", action="store_true", help="Use SODA3 POST instead of legacy GET")
    parser.add_argument("--limit", type=int, default=1000, help="Max rows (default 1000)")
    parser.add_argument("--where", type=str, default=None, help="SoQL WHERE clause")
    parser.add_argument("--out", type=str, help="Save JSON to this file")
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
    where = (args.where.strip() or None) if args.where else None
    data = call_soda3(token, args.limit, where) if args.soda3 else call_legacy(token, args.limit, where)

    print(f"Records returned: {len(data)}")
    if data:
        print(f"Columns: {', '.join(data[0].keys())}")
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print(f"Saved to {args.out}")
    if not args.quiet and data:
        print("\nFirst record:", json.dumps(data[0], indent=2))


if __name__ == "__main__":
    main()
