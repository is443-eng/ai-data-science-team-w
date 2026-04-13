# Manual QA checklist (Tool V2)

Run after code changes that touch loaders, risk model, orchestrator, or UI. Pair with `python3 -m pytest tests/` from the `Tool V2/` directory (network allowed for live parity tests). When preparing to submit, align with [`APP_SUBMISSION_READINESS.md`](APP_SUBMISSION_READINESS.md).

**Environment:** `SOCRATA_APP_TOKEN` (optional but recommended), `OLLAMA_API_KEY` for Overview agent insights and State tab summaries.

| Step | Page / area | What to verify |
|------|----------------|----------------|
| 1 | Sidebar | **Refresh data** runs without unhandled errors; **data as of** caption updates or shows message if loads fail. |
| 2 | **Overview** | Alarm / baseline / forecast snapshot renders; **AI agent insights** — after **Update my summaries**, Agent 2 reads as **state history + current risk** (metrics + excerpts); Agent 4 reads as a **simpler family version** of Agent 2; expanders match updated titles; changing **state** changes state-focused text when rows match. |
| 3 | **Historical trends** | Charts and NNDSS weekly view selector work; no blank page on valid data. |
| 4 | **Kindergarten coverage** | Map and table for selected year; year selector updates visuals. |
| 5 | **Wastewater vs NNDSS** | Detection frequency / comparison visuals load; year filters behave sensibly. |
| 6 | **State risk** | Table and map; **Choose a state** + AI summary (if key set). |
| 7 | **Forecast** | State outlook table; tiers and drivers columns populated when model ran. |
| 8 | Cross-cutting | Switch pages after refresh; no stale crash; optional debug panel off by default (`SHOW_DEBUG_UI`). |

**Regression vs baseline (optional):** Compare key metrics structure to `baseline/baseline_metrics.json` after intentional model or data pipeline changes.
