"""Mocked tests for wastewater and nndss tools."""
from __future__ import annotations

from unittest.mock import patch

import pandas as pd

from tools.nndss_tool import run as run_nndss
from tools.wastewater_tool import run as run_ww


def test_wastewater_ok():
    df = pd.DataFrame({"year": [2026], "week": [1]})
    with patch("tools.wastewater_tool.load_wastewater", return_value=(df, "ok")):
        out = run_ww({})
    assert out.status == "success"
    assert out.data["row_count"] == 1


def test_nndss_fail():
    with patch("tools.nndss_tool.load_nndss", return_value=(pd.DataFrame(), "fail")):
        out = run_nndss({})
    assert out.status == "error"
