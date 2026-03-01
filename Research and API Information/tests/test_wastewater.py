"""
Small validation: wastewater signal column exists and produces nonzero weekly aggregates.
Run from project root with the dashboard env active (e.g. pip install -r dashboard/requirements.txt):
  python -m pytest dashboard/tests/test_wastewater.py -v
  or: python dashboard/tests/test_wastewater.py
"""
from __future__ import annotations

import sys
from pathlib import Path

# Project root
ROOT = Path(__file__).resolve().parent.parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pandas as pd


def test_wastewater_signal_produces_nonzero_weekly_aggregates():
    """With synthetic data that has year, week, and a concentration column, _wastewater_national_weekly must return nonzero ww_signal."""
    from dashboard.risk import _wastewater_national_weekly

    ww = pd.DataFrame({
        "year": [2024, 2024, 2024, 2025],
        "week": [1, 1, 2, 1],
        "pcr_target_flowpop_lin": [0.5, 1.0, 2.0, 0.3],
    })
    agg = _wastewater_national_weekly(ww)
    assert not agg.empty
    assert "ww_signal" in agg.columns
    assert (agg["ww_signal"] > 0).any(), "At least one weekly aggregate should be > 0 when input has positive signal"


def test_wastewater_diagnostics_reports_signal_column():
    """get_wastewater_diagnostics must report the signal column and non-zero stats when data has values."""
    from dashboard.risk import get_wastewater_diagnostics

    ww = pd.DataFrame({
        "year": [2024],
        "week": [1],
        "pcr_target_avg_conc": [10.0],
    })
    diag = get_wastewater_diagnostics(ww)
    assert diag["signal_col"] == "pcr_target_avg_conc"
    assert diag["min"] == 10.0
    assert diag["max"] == 10.0
    assert diag["all_zero"] is False
    assert diag["non_null_pct"] == 100.0


def test_wastewater_uses_priority_signal_column():
    """When both 'value' and pcr_target_* exist, prefer 'value' (CDC-style priority)."""
    from dashboard.risk import _wastewater_national_weekly, _detect_ww_signal_column

    ww = pd.DataFrame({
        "year": [2024],
        "week": [1],
        "value": [5.0],
        "pcr_target_flowpop_lin": [99.0],
    })
    assert _detect_ww_signal_column(ww) == "value"
    agg = _wastewater_national_weekly(ww)
    assert not agg.empty and agg["ww_signal"].iloc[0] == 5.0


if __name__ == "__main__":
    test_wastewater_signal_produces_nonzero_weekly_aggregates()
    test_wastewater_diagnostics_reports_signal_column()
    test_wastewater_uses_priority_signal_column()
    print("Wastewater validation checks passed.")
