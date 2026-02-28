#!/usr/bin/env python3
"""
Test script: Run all 5 CDC API calls and verify cleaning operates as designed.
Saves each result to a pandas DataFrame. Requires SOCRATA_APP_TOKEN in .env.

Usage:
  python test_cdc_api_cleaning.py
  python test_cdc_api_cleaning.py --save-csv   # Also save DataFrames to data/raw/
"""

import os
import sys
from pathlib import Path

try:
    import pandas as pd
except ImportError:
    print("Install pandas: pip install pandas", file=sys.stderr)
    sys.exit(1)

# Ensure Shiny App V1 (script dir) is on path; load .env from project root
_SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = _SCRIPT_DIR.parent
sys.path.insert(0, str(_SCRIPT_DIR))
try:
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env")
except ImportError:
    pass

# No row cap: use Socrata max per request (50000)
FETCH_LIMIT = 50000


def run_nndss() -> pd.DataFrame:
    import call_cdc_nndss as m
    token = m.get_token()
    data = m.call_legacy(token, limit=FETCH_LIMIT, where=m.DEFAULT_WHERE)
    df = pd.DataFrame(data)
    return m.clean_nndss_data(df)


def run_child_vax() -> pd.DataFrame:
    import call_cdc_child_vax as m
    token = m.get_token()
    data = m.call_soda3(token, limit=FETCH_LIMIT, where=m.DEFAULT_WHERE)
    df = pd.DataFrame(data)
    return m.clean_child_vax_data(df)


def run_teen_vax() -> pd.DataFrame:
    import call_cdc_teen_vax as m
    token = m.get_token()
    data = m.call_legacy(token, limit=FETCH_LIMIT, where=m.DEFAULT_WHERE)
    df = pd.DataFrame(data)
    return m.clean_teen_vax_data(df)


def run_kindergarten_vax() -> pd.DataFrame:
    import call_cdc_kindergarten_vax as m
    token = m.get_token()
    data = m.call_legacy(token, limit=FETCH_LIMIT, where=m.DEFAULT_WHERE)
    df = pd.DataFrame(data)
    return m.clean_kindergarten_vax_data(df)


def run_wastewater() -> pd.DataFrame:
    import call_cdc_wastewater as m
    token = m.get_token()
    data = m.call_legacy(token, limit=FETCH_LIMIT, where=m.DEFAULT_WHERE)
    df = pd.DataFrame(data)
    return m.clean_wastewater_data(df)


def assert_nndss(df: pd.DataFrame) -> bool:
    """NNDSS: label in {Measles Indigenous, Measles Imported}, geo filter."""
    if df.empty:
        return True
    import call_cdc_nndss as m
    labels_ok = df["label"].astype(str).str.strip().isin(m.ALLOWED_LABELS).all()
    reporting_col = "Reporting Area" if "Reporting Area" in df.columns else "states"
    national = df[reporting_col].astype(str).str.strip() == m.NATIONAL_REPORTING_AREA
    loc_ok = df["location1"].notna() & (df["location1"].astype(str).str.strip() != "")
    geo_ok = (national | loc_ok).all()
    return bool(labels_ok and geo_ok)


def assert_child_vax(df: pd.DataFrame) -> bool:
    """Child vax: vaccine = ≥1 Dose MMR; national or state-level only (no HHS regions)."""
    if df.empty:
        return True
    import call_cdc_child_vax as m
    vax_ok = df["vaccine"].astype(str).str.strip().isin(m.MMR_VACCINE_VALUES).all()
    state_level = df["geography_type"].astype(str).str.strip() == m.GEOGRAPHY_TYPE_STATES
    national = df["geography"].astype(str).str.strip() == m.GEOGRAPHY_NATIONAL
    geo_ok = (state_level | national).all()
    return bool(vax_ok and geo_ok)


def assert_teen_vax(df: pd.DataFrame) -> bool:
    """Teen vax: vaccine = ≥2 Doses MMR; national or state-level only (no HHS regions)."""
    if df.empty:
        return True
    import call_cdc_teen_vax as m
    vax_ok = df["vaccine"].astype(str).str.strip().isin(m.MMR_VACCINE_VALUES).all()
    state_level = df["geography_type"].astype(str).str.strip() == m.GEOGRAPHY_TYPE_STATES
    national = df["geography"].astype(str).str.strip() == m.GEOGRAPHY_NATIONAL
    geo_ok = (state_level | national).all()
    return bool(vax_ok and geo_ok)


def assert_kindergarten_vax(df: pd.DataFrame) -> bool:
    """Kindergarten vax: vaccine in {MMR, MMR (PAC)}."""
    if df.empty:
        return True
    import call_cdc_kindergarten_vax as m
    return df["vaccine"].astype(str).str.strip().isin(m.MMR_VACCINE_VALUES).all()


def assert_wastewater(df: pd.DataFrame) -> bool:
    """Wastewater: pcr_target = MeV_WT (case-insensitive)."""
    if df.empty:
        return True
    import call_cdc_wastewater as m
    return (df["pcr_target"].astype(str).str.strip().str.upper() == m.MEASLES_PCR_TARGET.upper()).all()


def main():
    if not os.environ.get("SOCRATA_APP_TOKEN", "").strip():
        print("SOCRATA_APP_TOKEN not set. Add it to .env and re-run.", file=sys.stderr)
        sys.exit(1)

    import argparse
    parser = argparse.ArgumentParser(description="Test CDC API cleaning")
    parser.add_argument("--save-csv", action="store_true", help="Save each DataFrame to data/raw/")
    args = parser.parse_args()

    results = {}
    tests = [
        ("NNDSS", run_nndss, assert_nndss),
        ("Child Vax", run_child_vax, assert_child_vax),
        ("Teen Vax", run_teen_vax, assert_teen_vax),
        ("Kindergarten Vax", run_kindergarten_vax, assert_kindergarten_vax),
        ("Wastewater", run_wastewater, assert_wastewater),
    ]

    print("Running 5 CDC API calls (limit={} each)...".format(FETCH_LIMIT))
    print("-" * 50)

    for name, fetch_fn, assert_fn in tests:
        try:
            df = fetch_fn()
            results[name] = df
            passed = assert_fn(df)
            status = "PASS" if passed else "FAIL"
            print(f"  {name}: {len(df)} rows — {status}")
            if not passed:
                print(f"    WARNING: Cleaning assertion failed for {name}", file=sys.stderr)
        except Exception as e:
            print(f"  {name}: ERROR — {e}", file=sys.stderr)
            results[name] = None

    print("-" * 50)
    print("Done. All DataFrames stored in 'results' dict for inspection.")

    if args.save_csv:
        out_dir = PROJECT_ROOT / "data" / "raw"
        out_dir.mkdir(parents=True, exist_ok=True)
        for name, df in results.items():
            if df is not None and not df.empty:
                fname = name.lower().replace(" ", "_") + "_test.csv"
                path = out_dir / fname
                df.to_csv(path, index=False)
                print(f"Saved {path}")

    return results


if __name__ == "__main__":
    main()
