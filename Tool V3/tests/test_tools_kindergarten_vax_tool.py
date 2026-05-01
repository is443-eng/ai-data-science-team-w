"""Mocked tests for kindergarten_vax tool."""
from __future__ import annotations

from unittest.mock import patch

import pandas as pd

from tools.kindergarten_vax_tool import run


def test_kindergarten_success_shape():
    df = pd.DataFrame({"jurisdiction": ["X"], "coverage_pct": [90.0]})
    with patch("tools.kindergarten_vax_tool.load_kindergarten", return_value=(df, "ok")):
        out = run({"use_cache": True})
    assert out.tool_name == "kindergarten_vax"
    assert out.status == "success"
    assert out.data and out.data.get("row_count") == 1
    assert not out.errors


def test_kindergarten_fail_token():
    with patch("tools.kindergarten_vax_tool.load_kindergarten", return_value=(pd.DataFrame(), "fail")):
        out = run({})
    assert out.status == "error"
    assert out.errors
