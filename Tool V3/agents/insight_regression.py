"""
Deterministic (non-LLM) checks for Insight text regression smoke tests.

These checks are intentionally simple and cheap so they can run in CI.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, asdict


@dataclass
class ManualQualityCheckResult:
    has_data_as_of: bool
    has_baseline_tier: bool
    no_placeholders: bool
    within_length_limit: bool
    mentions_selected_state_when_required: bool
    passed: bool

    def to_json_dict(self) -> dict[str, bool]:
        return asdict(self)


_PLACEHOLDER_RE = re.compile(r"\b(TBD|TODO|lorem ipsum|\[insert|\[todo)\b", re.IGNORECASE)


def run_manual_quality_checks(
    *,
    text: str,
    data_as_of: str | None,
    baseline_tier: str | None,
    selected_state: str | None,
    max_chars: int = 1800,
) -> ManualQualityCheckResult:
    """
    Basic deterministic checks inspired by Module 09 manual QC.

    - Verify key context phrases are reflected in prose.
    - Catch common placeholder artifacts.
    - Keep text bounded for UI readability.
    """
    t = (text or "").strip()
    low = t.lower()

    dao = (data_as_of or "").strip()
    has_data_as_of = True if not dao else (dao.lower() in low)

    tier = (baseline_tier or "").strip()
    has_baseline_tier = True if not tier else (tier.lower() in low)

    state = (selected_state or "").strip()
    mentions_selected_state_when_required = True if not state else (state.lower() in low)

    no_placeholders = _PLACEHOLDER_RE.search(t) is None
    within_length_limit = len(t) <= max_chars

    passed = all(
        (
            has_data_as_of,
            has_baseline_tier,
            no_placeholders,
            within_length_limit,
            mentions_selected_state_when_required,
        )
    )

    return ManualQualityCheckResult(
        has_data_as_of=has_data_as_of,
        has_baseline_tier=has_baseline_tier,
        no_placeholders=no_placeholders,
        within_length_limit=within_length_limit,
        mentions_selected_state_when_required=mentions_selected_state_when_required,
        passed=passed,
    )
