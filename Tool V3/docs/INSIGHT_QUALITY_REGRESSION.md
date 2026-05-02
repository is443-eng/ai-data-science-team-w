# Insight Quality Regression

This file documents the "optional regression" workflow for Insight quality changes:

1. **Deterministic CI smoke checks** (cheap, no LLM calls)
2. **Prompt experiment comparisons** (score distributions across prompt variants)

## 1) Deterministic smoke checks

Use `run_manual_quality_checks()` in [`agents/insight_regression.py`](../agents/insight_regression.py) for basic guards:

- report includes `data_as_of` string
- report includes baseline tier string
- no placeholders (`TBD`, `TODO`, etc.)
- report stays within max character limit
- state summary mentions the selected state (when one is selected)

These checks are validated in [`tests/test_insight_regression.py`](../tests/test_insight_regression.py).

Run:

```bash
python3 -m pytest "Tool V3/tests/test_insight_regression.py" -q
```

## 2) Prompt experiment score comparison

Use [`scripts/insight_prompt_stats.py`](../scripts/insight_prompt_stats.py) to summarize and compare quality scores across prompt variants.

Input CSV must include:

- `prompt_variant`
- `overall_score`

Example:

```bash
python3 "Tool V3/scripts/insight_prompt_stats.py" --csv "Tool V3/data/insight_qc_scores.csv"
```

Output includes:

- per-variant `n`, mean, sd, min, max
- pairwise Welch t-statistics (directional comparison)

Notes:

- This script is intended for prompt iteration experiments, not per-request runtime.
- For publication-grade inference, move pairwise tests to a full stats stack (e.g., SciPy/pingouin or R equivalents).
