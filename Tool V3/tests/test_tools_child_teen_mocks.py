"""Mocked tests for child and teen vax tools (HTTP not called)."""
from __future__ import annotations

from unittest.mock import patch

import pandas as pd

from tools.child_vax_tool import run as run_child
from tools.teen_vax_tool import run as run_teen


def test_child_vax_missing_token():
    with patch("tools.child_vax_tool._get_token", return_value=None):
        out = run_child({})
    assert out.status == "error"
    assert any("SOCRATA" in e for e in out.errors)


def test_teen_vax_missing_token():
    with patch("tools.teen_vax_tool._get_token", return_value=None):
        out = run_teen({})
    assert out.status == "error"


def test_child_vax_success_mock_http():
    raw = [{"vaccine": "≥1 Dose MMR", "geography_type": "States/Local Areas", "geography": "Oregon"}]
    with patch("tools.child_vax_tool._get_token", return_value="fake"):
        with patch("tools.child_vax_tool.retry_http", return_value=raw):
            out = run_child({"limit": 10})
    assert out.status == "success"
    assert out.data and out.data.get("row_count") == 1


def test_teen_vax_success_mock_http():
    raw = [{"vaccine": "≥2 Doses MMR", "geography_type": "States/Local Areas", "geography": "United States"}]
    with patch("tools.teen_vax_tool._get_token", return_value="fake"):
        with patch("tools.teen_vax_tool.retry_http", return_value=raw):
            out = run_teen({})
    assert out.status == "success"
    assert out.data and out.data.get("row_count") >= 1
