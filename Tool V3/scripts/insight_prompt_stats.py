"""
Prompt experiment helper: summarize and compare QC scores by prompt variant.

Usage:
  python3 "Tool V3/scripts/insight_prompt_stats.py" --csv path/to/scores.csv

Expected columns:
  - prompt_variant (string; e.g., prompt_a, prompt_b)
  - overall_score (numeric; usually 1-5 from Insight QC)
"""
from __future__ import annotations

import argparse
import csv
import math
from collections import defaultdict
from statistics import mean, pstdev


def _safe_float(x: str) -> float | None:
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def load_scores(path: str) -> dict[str, list[float]]:
    grouped: dict[str, list[float]] = defaultdict(list)
    with open(path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        if "prompt_variant" not in reader.fieldnames or "overall_score" not in reader.fieldnames:
            raise ValueError("CSV must include columns: prompt_variant, overall_score")
        for row in reader:
            variant = (row.get("prompt_variant") or "").strip()
            score = _safe_float((row.get("overall_score") or "").strip())
            if not variant or score is None:
                continue
            grouped[variant].append(score)
    return dict(grouped)


def print_summary(grouped: dict[str, list[float]]) -> None:
    print("Prompt score summary")
    print("--------------------")
    for variant, vals in sorted(grouped.items()):
        if not vals:
            continue
        sd = pstdev(vals) if len(vals) > 1 else 0.0
        print(f"{variant:20s} n={len(vals):3d} mean={mean(vals):.3f} sd={sd:.3f} min={min(vals):.3f} max={max(vals):.3f}")


def _welch_t(v1: list[float], v2: list[float]) -> tuple[float, float]:
    """Return (t, approximate_df) for two groups."""
    n1, n2 = len(v1), len(v2)
    if n1 < 2 or n2 < 2:
        return math.nan, math.nan
    m1, m2 = mean(v1), mean(v2)
    s1, s2 = pstdev(v1), pstdev(v2)
    # pstdev uses population variance; convert to sample-like guard when n>1.
    var1 = (s1**2) * n1 / (n1 - 1)
    var2 = (s2**2) * n2 / (n2 - 1)
    denom = math.sqrt((var1 / n1) + (var2 / n2))
    if denom == 0:
        return math.nan, math.nan
    t = (m1 - m2) / denom
    num = (var1 / n1 + var2 / n2) ** 2
    den = ((var1 / n1) ** 2) / (n1 - 1) + ((var2 / n2) ** 2) / (n2 - 1)
    df = num / den if den else math.nan
    return t, df


def print_pairwise(grouped: dict[str, list[float]]) -> None:
    keys = sorted(grouped.keys())
    if len(keys) < 2:
        return
    print("\nPairwise Welch t-statistics (effect direction only)")
    print("----------------------------------------------------")
    for i in range(len(keys)):
        for j in range(i + 1, len(keys)):
            a, b = keys[i], keys[j]
            t, df = _welch_t(grouped[a], grouped[b])
            if math.isnan(t):
                print(f"{a} vs {b}: insufficient data")
            else:
                sign = "higher" if t > 0 else "lower"
                print(f"{a} vs {b}: t={t:.3f}, df≈{df:.1f} ({a} {sign} than {b})")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", required=True, help="CSV with prompt_variant,overall_score")
    args = ap.parse_args()

    grouped = load_scores(args.csv)
    if not grouped:
        print("No valid rows found.")
        return
    print_summary(grouped)
    print_pairwise(grouped)


if __name__ == "__main__":
    main()
