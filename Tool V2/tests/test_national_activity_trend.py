"""National weekly NNDSS trend helpers (Agent 3 temporal context)."""
from __future__ import annotations

import json

import pandas as pd

from risk import (
    compute_national_activity_trend_dict,
    format_national_activity_trend_from_records_json,
    format_selected_state_composite_snapshot,
    national_weekly_df_from_records_json,
    national_weekly_trend_json_from_agg,
)


def test_national_weekly_trend_json_from_agg_empty() -> None:
    assert national_weekly_trend_json_from_agg(pd.DataFrame()) is None
    assert national_weekly_trend_json_from_agg(pd.DataFrame({"a": [1]})) is None


def test_national_weekly_trend_json_from_agg_roundtrip() -> None:
    df = pd.DataFrame(
        [
            {"year": 2024, "week": 1, "cases": 2},
            {"year": 2024, "week": 2, "cases": 3},
        ]
    )
    js = national_weekly_trend_json_from_agg(df, max_weeks=104)
    assert js is not None
    back = national_weekly_df_from_records_json(js)
    assert len(back) == 2
    assert int(back.iloc[-1]["cases"]) == 3


def test_rolling_recent_vs_prior() -> None:
    rows = []
    for w in range(1, 13):
        rows.append({"year": 2024, "week": w, "cases": 1.0})
    for w in range(13, 25):
        rows.append({"year": 2024, "week": w, "cases": 10.0})
    df = pd.DataFrame(rows)
    d = compute_national_activity_trend_dict(df, weeks_compare=12)
    assert d["ok"]
    r = d["rolling"]
    assert r["recent_sum"] == 120.0
    assert r["prior_sum"] == 12.0
    assert r["pct_change_recent_vs_prior"] is not None
    assert abs(r["pct_change_recent_vs_prior"] - 900.0) < 0.01


def test_format_includes_yoy_and_ytd_when_multi_year() -> None:
    rows: list[dict] = []
    for y in (2022, 2023, 2024):
        for w in range(1, 11):
            rows.append({"year": y, "week": w, "cases": float(y)})
    js = json.dumps(rows)
    text = format_national_activity_trend_from_records_json(js, weeks_compare=4, band_weeks=4, years_compare=3)
    assert "National NNDSS weekly" in text
    assert "2022" in text and "2023" in text and "2024" in text
    assert "Year-to-date" in text or "YTD" in text


def test_empty_records_json_message() -> None:
    assert "not available" in format_national_activity_trend_from_records_json("[]").lower()


def test_format_selected_state_composite_snapshot_from_snapshot() -> None:
    extra = {"state_risk_snapshot": "total_risk_0_to_100: 50\nrisk_tier: medium"}
    out = format_selected_state_composite_snapshot(extra, "Ohio")
    assert "50" in out and "medium" in out


def test_format_selected_state_composite_snapshot_from_records() -> None:
    import json

    rows = [{"state": "Ohio", "total_risk": 40.0, "risk_tier": "medium", "cases_recent": 1.0}]
    out = format_selected_state_composite_snapshot({"state_risk_records_json": json.dumps(rows)}, "Ohio")
    assert "40" in out and "total_risk" in out


def test_ytd_and_yoy_na_when_year_not_in_weekly_extract() -> None:
    """Older calendar years with no rows in the serialized weekly series must be n/a, not 0."""
    rows: list[dict] = []
    for y in (2025, 2026):
        for w in range(1, 11):
            rows.append({"year": y, "week": w, "cases": 5.0})
    js = json.dumps(rows)
    df = national_weekly_df_from_records_json(js)
    d = compute_national_activity_trend_dict(df, weeks_compare=4, band_weeks=4, years_compare=5)
    assert d["ok"]
    ytd = d["ytd_by_year"]
    assert ytd.get(2022) is None
    assert ytd.get(2023) is None
    assert ytd.get(2024) is None
    assert ytd.get(2025) is not None
    assert ytd.get(2026) is not None
    text = format_national_activity_trend_from_records_json(js, weeks_compare=4, band_weeks=4, years_compare=5)
    assert "n/a" in text.lower()
    assert "Important:" in text
    assert "BASELINE ATTRIBUTION" in text


def test_single_year_insufficient_prior_window_note() -> None:
    rows = [{"year": 2024, "week": w, "cases": 1.0} for w in range(1, 15)]
    js = json.dumps(rows)
    d = compute_national_activity_trend_dict(national_weekly_df_from_records_json(js), weeks_compare=12)
    assert d["ok"]
    assert d["rolling"]["prior_sum"] is None or any("Prior window" in n for n in d.get("notes", []))
