"""Live parity: tool row counts match ``loaders`` when ``SOCRATA_APP_TOKEN`` is set."""
from __future__ import annotations

import os

import pytest

from loaders import clear_cache, load_kindergarten, load_nndss, load_wastewater


@pytest.mark.skipif(not (os.environ.get("SOCRATA_APP_TOKEN") or "").strip(), reason="SOCRATA_APP_TOKEN not set")
def test_kindergarten_tool_matches_loader():
    from tools.kindergarten_vax_tool import run as run_kg

    clear_cache()
    df, st = load_kindergarten(use_cache=False)
    out = run_kg({"use_cache": False})
    assert st == "ok" and out.status == "success"
    assert out.data["row_count"] == len(df)


@pytest.mark.skipif(not (os.environ.get("SOCRATA_APP_TOKEN") or "").strip(), reason="SOCRATA_APP_TOKEN not set")
def test_wastewater_tool_matches_loader():
    from tools.wastewater_tool import run as run_ww

    clear_cache()
    df, st = load_wastewater(use_cache=False)
    out = run_ww({"use_cache": False})
    assert st == "ok" and out.status == "success"
    assert out.data["row_count"] == len(df)


@pytest.mark.skipif(not (os.environ.get("SOCRATA_APP_TOKEN") or "").strip(), reason="SOCRATA_APP_TOKEN not set")
def test_nndss_tool_matches_loader():
    from tools.nndss_tool import run as run_n

    clear_cache()
    df, st = load_nndss(use_cache=False)
    out = run_n({"use_cache": False})
    assert st == "ok" and out.status == "success"
    assert out.data["row_count"] == len(df)
