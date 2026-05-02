"""Insight rubric parsing and pass thresholds (no LLM)."""
from __future__ import annotations

import json

import pytest

from agents.insight_quality import (
    compute_passed,
    overall_from_scores,
    parse_insight_qc_json,
)


def test_parse_insight_qc_json_pure() -> None:
    payload = {
        "accurate": True,
        "accuracy": 4,
        "formality": 4,
        "faithfulness": 5,
        "clarity": 4,
        "succinctness": 3,
        "relevance": 4,
        "details": "ok",
    }
    raw = json.dumps(payload)
    assert parse_insight_qc_json(raw) == payload


def test_parse_insight_qc_json_embedded() -> None:
    raw = 'Here is JSON:\n```\n{"accurate": false, "accuracy": 2, "formality": 3, "faithfulness": 2, "clarity": 3, "succinctness": 3, "relevance": 4, "details": "x"}\n```'
    d = parse_insight_qc_json(raw)
    assert d["accurate"] is False


def test_overall_from_scores() -> None:
    s = {"accuracy": 4.0, "faithfulness": 2.0, "clarity": 4.0, "succinctness": 4.0, "relevance": 4.0, "formality": 4.0}
    assert overall_from_scores(s) == pytest.approx(22.0 / 6.0, rel=1e-3)


def test_compute_passed_threshold(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("INSIGHT_QC_MIN_OVERALL", "3.0")
    monkeypatch.setenv("INSIGHT_QC_REQUIRE_ACCURATE", "1")
    assert compute_passed(overall=4.0, accurate=True) is True
    assert compute_passed(overall=2.5, accurate=True) is False
    assert compute_passed(overall=4.0, accurate=False) is False

    monkeypatch.setenv("INSIGHT_QC_REQUIRE_ACCURATE", "0")
    assert compute_passed(overall=4.0, accurate=False) is True
