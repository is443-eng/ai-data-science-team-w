"""
Optional AI rubric for Insights text (Module 09–style JSON QC).

Ground-truth context is built by the orchestrator from AgentContext (compact tool summary +
dashboard metrics). Thresholds come from environment variables.
"""
from __future__ import annotations

import json
import os
import re
from typing import Any, Literal

from contracts.schemas import InsightQCResult
from ollama_client import chat_completion
from utils.logging_config import get_logger

logger = get_logger("insight_quality")

_ROLE_USER_LABEL = {"national": "National summary", "state": "State summary"}

LIKERT_KEYS = (
    "accuracy",
    "formality",
    "faithfulness",
    "clarity",
    "succinctness",
    "relevance",
)


def insight_qc_enabled() -> bool:
    v = (os.getenv("INSIGHT_QC_ENABLED") or "").strip().lower()
    return v in ("1", "true", "yes", "on")


def _min_overall() -> float:
    raw = (os.getenv("INSIGHT_QC_MIN_OVERALL") or "3.0").strip()
    try:
        return max(1.0, min(5.0, float(raw)))
    except (TypeError, ValueError):
        return 3.0


def _require_accurate() -> bool:
    v = (os.getenv("INSIGHT_QC_REQUIRE_ACCURATE") or "1").strip().lower()
    return v not in ("0", "false", "no", "off")


def _system_prompt() -> str:
    return (
        "You are a quality control validator for public-health dashboard prose. "
        "You must respond with a single valid JSON object only—no markdown fences, no commentary."
    )


def _user_prompt(
    role: Literal["national", "state"],
    report_text: str,
    source_context: str,
) -> str:
    label = _ROLE_USER_LABEL[role]
    return f"""You validate an AI-written **{label}** for a measles surveillance dashboard.
The **Source context** is authoritative: tool outputs, data_as_of, baseline tier, and state risk blocks.
The **Report text** must not invent case counts, percentages, dates, or coverage numbers beyond what the context supports.

Source context:
{source_context}

Report text to validate:
{report_text}

Return valid JSON in exactly this shape (numbers 1–5 for Likert fields):
{{
  "accurate": true or false,
  "accuracy": <1-5>,
  "formality": <1-5>,
  "faithfulness": <1-5>,
  "clarity": <1-5>,
  "succinctness": <1-5>,
  "relevance": <1-5>,
  "details": "<=50 words explaining issues or confirming quality>"
}}

Criteria:
- **accurate** (boolean): true only if no numeric or factual claim contradicts the source context.
- **accuracy** (1–5): degree of correct interpretation of the supplied data.
- **formality**: appropriate neutral public-health tone vs casual.
- **faithfulness**: claims grounded in context vs unsupported assertions.
- **clarity**, **succinctness**, **relevance**: writing quality for this UI.
"""


def parse_insight_qc_json(raw: str) -> dict[str, Any]:
    """Extract first JSON object from model output (handles extra prose)."""
    text = (raw or "").strip()
    if not text:
        raise ValueError("empty response")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass
    m = re.search(r"\{[\s\S]*\}", text)
    if not m:
        raise ValueError("no JSON object found")
    return json.loads(m.group(0))


def _coerce_bool(v: Any) -> bool | None:
    if isinstance(v, bool):
        return v
    if isinstance(v, str):
        s = v.strip().lower()
        if s in ("true", "1", "yes"):
            return True
        if s in ("false", "0", "no"):
            return False
    return None


def _coerce_likert(v: Any) -> float | None:
    try:
        n = float(v)
    except (TypeError, ValueError):
        return None
    if 1.0 <= n <= 5.0:
        return n
    return None


def overall_from_scores(scores: dict[str, Any]) -> float | None:
    vals: list[float] = []
    for k in LIKERT_KEYS:
        x = _coerce_likert(scores.get(k))
        if x is not None:
            vals.append(x)
    if not vals:
        return None
    return round(sum(vals) / len(vals), 2)


def compute_passed(*, overall: float | None, accurate: bool | None) -> bool | None:
    if overall is None:
        return None
    min_o = _min_overall()
    ok = overall >= min_o
    if _require_accurate() and accurate is False:
        ok = False
    return ok


def run_insight_qc(
    role: Literal["national", "state"],
    report_text: str,
    source_context: str,
) -> InsightQCResult:
    """
    Call the configured LLM once with a rubric prompt; parse JSON into InsightQCResult.

    Does not catch-all guard production prose—thresholds are advisory (logging / UI expander).
    """
    text = (report_text or "").strip()
    if not text:
        return InsightQCResult(role=role, status="skipped", error_message="empty report text")

    ctx_block = (source_context or "").strip()
    if len(ctx_block) > 24000:
        ctx_block = ctx_block[:24000] + "\n... (truncated)"

    user = _user_prompt(role, text, ctx_block)
    raw: str | None = None
    try:
        raw = chat_completion(_system_prompt(), user, timeout_s=90)
    except Exception as e:
        logger.exception("insight_qc LLM call failed role=%s", role)
        return InsightQCResult(
            role=role,
            status="error",
            error_message=f"LLM error: {e}",
        )

    if not (raw or "").strip():
        return InsightQCResult(
            role=role,
            status="error",
            error_message="LLM returned no text",
        )

    try:
        data = parse_insight_qc_json(raw)
    except (json.JSONDecodeError, ValueError) as e:
        logger.warning("insight_qc JSON parse failed role=%s err=%s", role, e)
        return InsightQCResult(
            role=role,
            status="error",
            error_message=f"Could not parse QC JSON: {e}",
        )

    accurate = _coerce_bool(data.get("accurate"))
    scores: dict[str, Any] = {}
    for k in LIKERT_KEYS:
        x = _coerce_likert(data.get(k))
        if x is not None:
            scores[k] = x
    overall = overall_from_scores(scores)
    details = data.get("details")
    if details is not None:
        details = str(details)[:500]

    passed = compute_passed(overall=overall, accurate=accurate)

    return InsightQCResult(
        role=role,
        status="success",
        passed=passed,
        overall_score=overall,
        accurate=accurate,
        scores=scores,
        details=details if isinstance(details, str) else None,
    )
