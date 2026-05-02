"""Deterministic manual QC checks for CI smoke."""
from __future__ import annotations

from agents.insight_regression import run_manual_quality_checks


def test_manual_checks_pass_for_grounded_text() -> None:
    text = (
        "Data as of: 2026-05-01. Baseline risk tier: medium. "
        "Ohio remains in watch conditions based on current context."
    )
    out = run_manual_quality_checks(
        text=text,
        data_as_of="2026-05-01",
        baseline_tier="medium",
        selected_state="Ohio",
    )
    assert out.passed is True
    assert out.no_placeholders is True


def test_manual_checks_fail_when_required_fields_missing() -> None:
    text = "National summary TBD."
    out = run_manual_quality_checks(
        text=text,
        data_as_of="2026-05-01",
        baseline_tier="high",
        selected_state="Texas",
        max_chars=40,
    )
    assert out.passed is False
    assert out.has_data_as_of is False
    assert out.has_baseline_tier is False
    assert out.mentions_selected_state_when_required is False
    assert out.no_placeholders is False
