"""Wastewater state rollup: CDC column renames (state_territory vs wwtp_jurisdiction)."""
from __future__ import annotations

import pandas as pd


def test_wastewater_state_weekly_accepts_state_territory() -> None:
    from risk import _wastewater_state_weekly

    df = pd.DataFrame(
        {
            "state_territory": ["Ohio", "Ohio"],
            "year": [2024, 2024],
            "week": [10, 11],
            "pcr_target_avg_conc_lin": [1.0, 3.0],
        }
    )
    out = _wastewater_state_weekly(df)
    assert not out.empty
    assert set(out["state"].astype(str).str.upper().unique()) == {"OH"}
    assert "ww_signal" in out.columns


def test_wastewater_state_weekly_still_accepts_wwtp_jurisdiction() -> None:
    from risk import _wastewater_state_weekly

    df = pd.DataFrame(
        {
            "wwtp_jurisdiction": ["Ohio", "Ohio"],
            "year": [2024, 2024],
            "week": [10, 11],
            "pcr_target_avg_conc_lin": [1.0, 3.0],
        }
    )
    out = _wastewater_state_weekly(df)
    assert not out.empty
