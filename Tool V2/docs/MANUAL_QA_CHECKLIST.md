# Manual QA checklist (Tool V2)

Run after code changes that touch loaders, risk model, orchestrator, or UI. Pair with `python3 -m pytest tests/` from the `Tool V2/` directory (network allowed for live parity tests). When preparing to submit, align with [`APP_SUBMISSION_READINESS.md`](APP_SUBMISSION_READINESS.md).

**Environment:** `SOCRATA_APP_TOKEN` (optional but recommended for CDC pulls). For **Insights**: **`OPENAI_API_KEY`** (recommended; enables tool calling in agents) or **`OLLAMA_API_KEY`**. Optional `OPENAI_MODEL`.

| Step | Page / area | What to verify |
|------|----------------|----------------|
| 1 | Sidebar | **Refresh data** runs without unhandled errors; **data as of** caption updates or shows message if loads fail. |
| 2 | **Overview** | Baseline gauge + metrics render. **Insights:** Tap **Generate insights** — Agent 1 data check expands; with LLM on, **National summary** (Agent 5) appears; with a **state** selected, **state summary** (Agent 4) appears below national. State text should not fully duplicate the national paragraph (prompts de-duplicate). Changing **State (optional)** and re-running changes state-scoped content when tool rows match. |
| 3 | **Historical trends** | Charts and NNDSS weekly view selector work; baseline expander reflects harmonized score when applicable. |
| 4 | **Kindergarten coverage** | Map and table for selected year; year selector updates visuals. |
| 5 | **Wastewater vs NNDSS** | Detection frequency / comparison visuals load; year filters behave sensibly. |
| 6 | **State risk** | Choropleth and table; **risk tier** shows spread (tertiles). Expander describes composite + tertile semantics. |
| 7 | **Forecast** | State outlook table; tiers and scores populated when model ran. |
| 8 | Cross-cutting | Switch pages after refresh; no stale crash; optional debug panel off by default (`SHOW_DEBUG_UI`). |

**Regression vs baseline (optional):** Compare key metrics structure to `baseline/baseline_metrics.json` after intentional model or data pipeline changes.
