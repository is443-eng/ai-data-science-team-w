"""State risk leaderboard formatting for Agent 3."""
from __future__ import annotations

import json

import pandas as pd


def test_format_state_risk_leaderboard_sorts_by_total_risk() -> None:
    from risk import format_state_risk_leaderboard, format_state_risk_leaderboard_from_records_json

    df = pd.DataFrame(
        [
            {"state": "A", "total_risk": 10.0, "risk_tier": "low", "cases_recent": 0.0, "coverage": 95.0},
            {"state": "B", "total_risk": 80.0, "risk_tier": "high", "cases_recent": 5.0, "coverage": 80.0},
            {"state": "C", "total_risk": 50.0, "risk_tier": "medium", "cases_recent": 2.0, "coverage": 90.0},
        ]
    )
    text = format_state_risk_leaderboard(df, limit=2)
    assert "B" in text and "total_risk=80" in text
    assert "C" in text
    assert "A" not in text.split("\n")[0]  # A is lowest; top 2 are B, C

    js = df.to_json(orient="records")
    text2 = format_state_risk_leaderboard_from_records_json(js, limit=2)
    assert "B" in text2


def test_format_state_risk_leaderboard_empty() -> None:
    from risk import format_state_risk_leaderboard

    assert "No state risk" in format_state_risk_leaderboard(pd.DataFrame(), limit=5)


def test_format_state_tier_counts_from_records_json() -> None:
    from risk import format_state_tier_counts_from_records_json

    records = [
        {"state": "A", "risk_tier": "low"},
        {"state": "B", "risk_tier": "high"},
        {"state": "C", "risk_tier": "high"},
    ]
    t = format_state_tier_counts_from_records_json(json.dumps(records))
    assert "high: 2 states" in t
    assert "low: 1 states" in t


def test_assign_state_risk_tiers_equal_count_tertiles() -> None:
    """51 jurisdictions → ~17 high, ~17 medium, ~17 low when scores differ."""
    from collections import Counter

    import numpy as np
    import pandas as pd

    from risk import assign_state_risk_tiers_from_total_risk

    n = 51
    tr = pd.Series(np.linspace(10.0, 60.0, n))
    tiers = assign_state_risk_tiers_from_total_risk(tr)
    c = Counter(tiers.tolist())
    assert c["high"] == 17 and c["medium"] == 17 and c["low"] == 17


def test_harmonize_baseline_caps_against_max_state_total_risk() -> None:
    """Overview baseline should not read ~100 when state composite max is far lower (same 0–100 display)."""
    from risk import BASELINE_STATE_COMPOSITE_HEADROOM, harmonize_baseline_with_state_composite

    sr = pd.DataFrame({"total_risk": [20.0, 52.7, 10.0]})
    s, tier, note = harmonize_baseline_with_state_composite(100.0, "high", sr)
    assert s == 52.7 + BASELINE_STATE_COMPOSITE_HEADROOM
    assert tier == "high"
    assert note and "capped" in note.lower()


def test_baseline_recent_five_is_chronological_not_row_order() -> None:
    """Rows out of year order; last five *calendar* years should still get mean 100."""
    from risk import get_baseline_risk_components

    df = pd.DataFrame(
        {
            "Year": [2024, 2019, 2020, 2023, 2021, 2022, 2015, 2016, 2017, 2018],
            "Measles Cases": [100, 1, 100, 100, 100, 100, 1, 1, 1, 1],
        }
    )
    comp = get_baseline_risk_components(df, pd.DataFrame())
    assert comp["recent_5yr_avg"] == 100.0
    assert comp.get("interpretation_note")


def test_adjust_baseline_ytd_elevates_tier_when_ytd_exceeds_recent_annual_benchmark() -> None:
    """When NNDSS YTD exceeds recent 5-year annual average, tier/score rise (Overview aligns with surveillance)."""
    from risk import _adjust_baseline_for_nndss_ytd

    per_week = 7571.0 / 13.0
    rows = [{"year": 2026, "week": w, "cases": per_week} for w in range(1, 14)]
    rows += [{"year": 2025, "week": w, "cases": 5.0} for w in range(1, 14)]
    nat = pd.DataFrame(rows)
    tier, score, note = _adjust_baseline_for_nndss_ytd("low", 7.5, 745.0, nat)
    assert tier == "high"
    assert score >= 55.0
    assert "7571" in note or "NNDSS" in note or "YTD" in note


def test_get_state_risk_df_sparse_kg_multi_state_nndss_full_us_and_case_states() -> None:
    """Sparse kindergarten + many NNDSS jurisdictions: all US rows, every case-bearing state listed."""
    from risk import get_state_risk_df
    from utils.state_maps import STATE_TO_ABBR

    kg = pd.DataFrame(
        [
            {"state": "California", "coverage_pct": 92.0},
            {"state": "Colorado", "coverage_pct": 88.0},
        ]
    )
    rows_nndss = []
    for week in (13, 12, 11, 10):
        for state, c in [
            ("California", 10.0),
            ("Texas", 5.0),
            ("New York", 8.0),
            ("Florida", 3.0),
        ]:
            rows_nndss.append(
                {"Reporting Area": state, "year": 2026, "week": week, "m1": c}
            )
    nndss = pd.DataFrame(rows_nndss)

    df = get_state_risk_df(kg, nndss, None)

    assert len(df) == len(STATE_TO_ABBR)
    by_state = df.set_index("state")["cases_recent"].to_dict()
    for name in ("California", "Texas", "New York", "Florida"):
        assert by_state.get(name, 0) > 0, f"expected NNDSS cases for {name}"
    # Texas not in kindergarten: imputed coverage = median of CA/CO kg values
    assert df.loc[df["state"] == "Texas", "coverage"].iloc[0] == 90.0


def test_get_state_risk_df_empty_kg_nndss_still_returns_states() -> None:
    """No kindergarten rows but state-level NNDSS activity still yields a full state table."""
    from risk import get_state_risk_df
    from utils.state_maps import STATE_TO_ABBR

    rows_nndss = []
    for week in (5, 4, 3, 2):
        rows_nndss.append({"Reporting Area": "Ohio", "year": 2026, "week": week, "m1": 12.0})
        rows_nndss.append({"Reporting Area": "Michigan", "year": 2026, "week": week, "m1": 7.0})
    nndss = pd.DataFrame(rows_nndss)

    df = get_state_risk_df(pd.DataFrame(), nndss, None)
    assert len(df) == len(STATE_TO_ABBR)
    assert df.loc[df["state"] == "Ohio", "cases_recent"].iloc[0] > 0


def test_get_state_risk_df_empty_kg_empty_nndss_still_full_us_for_leaderboard() -> None:
    """No kg and no state-level case signal still yields 51 rows so agents can name top states (ties broken by name)."""
    from risk import get_state_risk_df, format_state_risk_leaderboard
    from utils.state_maps import STATE_TO_ABBR

    df = get_state_risk_df(pd.DataFrame(), pd.DataFrame(), None)
    assert len(df) == len(STATE_TO_ABBR)
    text = format_state_risk_leaderboard(df, limit=3)
    lines = [ln for ln in text.split("\n") if ln.strip().startswith("- ")]
    assert len(lines) == 3
    assert "Alabama" in text  # first state alphabetically among max ties after sort
