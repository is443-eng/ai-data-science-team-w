"""
Capture deterministic baseline metrics from loaders (Segment 0 regression reference).
Run from repo:  python scripts/capture_baseline.py
CWD should be Tool V3 (or pass --out).
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

APP_DIR = Path(__file__).resolve().parent.parent
if str(APP_DIR) not in sys.path:
    sys.path.insert(0, str(APP_DIR))


def _historical_summary(hist):
    import pandas as pd

    if hist is None or hist.empty:
        return {"columns": [], "year_min": None, "year_max": None}
    cols = list(hist.columns)
    yr_col = next((c for c in hist.columns if str(c).lower() == "year"), None)
    if yr_col is None:
        return {"columns": cols, "year_min": None, "year_max": None}
    y = pd.to_numeric(hist[yr_col], errors="coerce").dropna()
    if y.empty:
        return {"columns": cols, "year_min": None, "year_max": None}
    return {"columns": cols, "year_min": int(y.min()), "year_max": int(y.max())}


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--out", type=Path, default=APP_DIR / "baseline" / "baseline_metrics.json")
    args = p.parse_args()

    from loaders import load_all

    hist, kg, ww, nndss, load_status, data_as_of = load_all(use_cache=False)
    payload = {
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "data_as_of": data_as_of,
        "load_status": load_status,
        "row_counts": {
            "historical": len(hist) if hist is not None else 0,
            "kindergarten": len(kg) if kg is not None else 0,
            "wastewater": len(ww) if ww is not None else 0,
            "nndss": len(nndss) if nndss is not None else 0,
        },
        "historical_csv": _historical_summary(hist),
    }
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print("Wrote", args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
