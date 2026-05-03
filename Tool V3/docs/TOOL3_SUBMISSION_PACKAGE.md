# TOOL3 — App V3 submission package

Permanent URL prefix used below: `**main**` branch, repo **[is443-eng/ai-data-science-team-w](https://github.com/is443-eng/ai-data-science-team-w)** (`https://github.com/is443-eng/ai-data-science-team-w/blob/main/…`). All repository paths are spelled so exported **PDF readers can open links** without a repository clone.

---

## Links


| Item                              | URL                                                                                                                                                              |
| --------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| GitHub repository (main branch)   | [https://github.com/is443-eng/ai-data-science-team-w](https://github.com/is443-eng/ai-data-science-team-w)                                                       |
| Live deployed app (Posit Connect) | [https://connect.systems-apps.com/content/b8cfc1fa-8eb0-4c2e-ba98-b5f06837e933/](https://connect.systems-apps.com/content/b8cfc1fa-8eb0-4c2e-ba98-b5f06837e933/) |
| Live Video App Demo               | [https://youtu.be/bpEJRjsjYyc](https://youtu.be/bpEJRjsjYyc)                                                                                                     |
| Demo Final Script (GitHub)        | [Demo Final Script.md](https://github.com/is443-eng/ai-data-science-team-w/blob/main/Tool%20V3/docs/Demo%20Final%20Script.md)                                    |


---

## Rubric mapping (TOOL3 — 100 pts)


| Rubric item (from TOOL3)                         | How the shipped app addresses it                                                                                                                                                                                                                                                                                                                                                                                                                                                                                |
| ------------------------------------------------ | --------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **50 pts — Production-ready functional app**     |                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| Stakeholder alignment (10)                       | Public-health–oriented **Measles** dashboard: CDC open data, plain-language **Overview**, **state/national** insights, risk tiers and forecast context—not clinical advice; disclaimer in-app.                                                                                                                                                                                                                                                                                                                  |
| Clarity (10)                                     | Streamlit **sidebar** navigation, **Data as of** and per-source load lines, **Overview** baseline + **Insights** with optional state; expanders for methodology.                                                                                                                                                                                                                                                                                                                                                |
| Streamlining (10)                                | Focused tab set (Overview, Historical, Kindergarten, Wastewater vs NNDSS, State risk, Forecast); LLM optional via **Include AI-written summaries**; no duplicate product surfaces.                                                                                                                                                                                                                                                                                                                              |
| Efficiency (10)                                  | **1-hour** CDC/tool fetch caching, **session reuse** of model outputs within TTL, **Generate insights** reuses cached Socrata rows when available; **Python 3.12.4** on Connect.                                                                                                                                                                                                                                                                                                                                |
| Reliability (10)                                 | **57** automated tests (`Tool V3/tests/`); partial tool/LLM failure handling in orchestrator; graceful empty states; **tornado** and explicit **scipy** in [requirements.txt](https://github.com/is443-eng/ai-data-science-team-w/blob/main/Tool%20V3/requirements.txt) for Connect builds.                                                                                                                                                                                                                     |
| **20 pts — Quality control and validation**      |                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| QC implementation (10)                           | **Insight quality rubric** (`INSIGHT_QC_ENABLED=1`) scores national/state summaries; **refinement loop** (`INSIGHT_REFINEMENT_`*) with documented env vars.                                                                                                                                                                                                                                                                                                                                                     |
| Evidence of AI performance (10)                  | **Insight quality expander** on Overview when QC runs; **insight regression** tests ([INSIGHT_QUALITY_REGRESSION.md](https://github.com/is443-eng/ai-data-science-team-w/blob/main/Tool%20V3/docs/INSIGHT_QUALITY_REGRESSION.md)); `InsightQCResult` in [INTERFACE_CONTRACTS.md](https://github.com/is443-eng/ai-data-science-team-w/blob/main/Tool%20V3/docs/INTERFACE_CONTRACTS.md) / `[contracts/schemas.py](https://github.com/is443-eng/ai-data-science-team-w/blob/main/Tool%20V3/contracts/schemas.py)`. |
| **20 pts — Presentation**                        |                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| Live demonstration (10)                          | [Demo Script Talking Points](https://github.com/is443-eng/ai-data-science-team-w/blob/main/Tool%20V3/docs/Demo%20Script%20Talking%20Points.md) supports a 3–5 minute walkthrough of the **deployed** URL above.                                                                                                                                                                                                                                                                                                 |
| Presentation materials (10)                      | Demo script + (team provides slides or video per course / DL policy in Canvas).                                                                                                                                                                                                                                                                                                                                                                                                                                 |
| **10 pts — Deployed app link**                   | **Working** Posit Connect URL in the table: direct content link above; Connect dashboard: [open in Connect (`#/apps/b8cfc1fa-…`)](https://connect.systems-apps.com/connect/#/apps/b8cfc1fa-8eb0-4c2e-ba98-b5f06837e933)                                                                                                                                                                                                                                                                                         |
| **Agentic loop** (course overview; design yours) | After tools run, **five LLM stages**: Agent **1** (tool runner) → **2 ∥ 3** (state vs national analysts) → **4 ∥ 5** (state vs national reporters). Optional **insight QC / refinement** env toggles. See [ARCHITECTURE.md](https://github.com/is443-eng/ai-data-science-team-w/blob/main/Tool%20V3/docs/ARCHITECTURE.md), `[agents/orchestrator.py](https://github.com/is443-eng/ai-data-science-team-w/blob/main/Tool%20V3/agents/orchestrator.py)`.                                                          |


---

## Technical documentation

### System architecture

- **Frontend:** Streamlit (`app.py`); **Overview** integrates `ui/agent_insights.py` (**Generate insights**).
- **Data:** `loaders.py` + `tools/`* for CDC; `risk.py` for alarm model, aggregates, **state composite** (`get_state_risk_df`), baseline, forecast.
- **Orchestration:** `agents/orchestrator.py` — Agent 1 → Agents 2 ∥ 3 → Agents 4 ∥ 5; optional `InsightQCResult` on `OrchestratorRun`. State risk JSON rebuilt from **Agent 1** tool payloads when possible.
- **Prompts:** `prompts/*.md` + `prompts/loader.py`; `shared_guardrails.md`.

### Tool functions (names and purpose)


| Tool name          | Purpose                      | Returns (conceptually)        |
| ------------------ | ---------------------------- | ----------------------------- |
| `child_vax`        | Child (0–35 mo) MMR coverage | Rows + metadata per contracts |
| `kindergarten_vax` | Kindergarten MMR coverage    | Rows + metadata               |
| `teen_vax`         | Teen MMR series              | Rows + metadata               |
| `wastewater`       | Wastewater / surveillance    | Rows + metadata               |
| `nndss`            | NNDSS case line lists        | Rows + metadata               |


Exact fields: [INTERFACE_CONTRACTS.md](https://github.com/is443-eng/ai-data-science-team-w/blob/main/Tool%20V3/docs/INTERFACE_CONTRACTS.md).

### Technical details

- **Python:** [Tool V3/requirements.txt](https://github.com/is443-eng/ai-data-science-team-w/blob/main/Tool%20V3/requirements.txt) (includes **streamlit**, **tornado** for Connect runtime, **scipy** for `risk.py`, **scikit-learn**, etc.); bundle targets **Python 3.12.4**; `[.python-version](https://github.com/is443-eng/ai-data-science-team-w/blob/main/Tool%20V3/.python-version)` and `[deployment/deploy_me.py](https://github.com/is443-eng/ai-data-science-team-w/blob/main/Tool%20V3/deployment/deploy_me.py)` defaults align with the Connect image.
- **Secrets:** `OPENAI_API_KEY` (recommended), `OLLAMA_API_KEY` (fallback), optional `SOCRATA_APP_TOKEN`, `OPENAI_MODEL`; deploy keys (`POSIT_PUBLISHER_KEY`, etc.) only on the **publisher** machine — use Connect **Vars** and `deploy_me.py` `**-E`** forwarding. Never commit secrets.
- **Repo layout:** `Tool V3/` is the app root: `contracts/`, `tools/`, `agents/`, `prompts/`, `ui/`, `tests/`, `docs/`, `deployment/`.

### Usage instructions (deployed app)

1. Open the **live URL** (see Links table).
2. Use **Refresh data** in the sidebar to bypass cache and pull fresh CDC data when needed.
3. On **Overview**, optional **State (optional)** and **Generate insights** (requires server LLM keys unless AI summaries are off).
4. Use other tabs for charts, maps, and forecast; see [USAGE_INSTRUCTIONS.md](https://github.com/is443-eng/ai-data-science-team-w/blob/main/Tool%20V3/docs/USAGE_INSTRUCTIONS.md).

*Password:* not required unless the team adds optional auth (document in submission if added).

---

## Team members by role


| Name           | Role (examples)         |
| -------------- | ----------------------- |
| Jonathan Lloyd | Frontend and Deployment |
| Ian Steigmeyer | Backend and Agents      |


---

## Pointers for grading

- **Orchestration + tools:** `[agents/orchestrator.py](https://github.com/is443-eng/ai-data-science-team-w/blob/main/Tool%20V3/agents/orchestrator.py)`, `[tools/registry.py](https://github.com/is443-eng/ai-data-science-team-w/blob/main/Tool%20V3/tools/registry.py)`, `[tests/test_orchestrator.py](https://github.com/is443-eng/ai-data-science-team-w/blob/main/Tool%20V3/tests/test_orchestrator.py)`.
- **UI:** `[app.py](https://github.com/is443-eng/ai-data-science-team-w/blob/main/Tool%20V3/app.py)`, `[ui/agent_insights.py](https://github.com/is443-eng/ai-data-science-team-w/blob/main/Tool%20V3/ui/agent_insights.py)`.
- **Risk + state table:** `[risk.py](https://github.com/is443-eng/ai-data-science-team-w/blob/main/Tool%20V3/risk.py)`, `[tests/test_risk_leaderboard.py](https://github.com/is443-eng/ai-data-science-team-w/blob/main/Tool%20V3/tests/test_risk_leaderboard.py)`.
- **QC / regression:** `[agents/insight_quality.py](https://github.com/is443-eng/ai-data-science-team-w/blob/main/Tool%20V3/agents/insight_quality.py)`, `[tests/test_insight_quality.py](https://github.com/is443-eng/ai-data-science-team-w/blob/main/Tool%20V3/tests/test_insight_quality.py)`, [INSIGHT_QUALITY_REGRESSION.md](https://github.com/is443-eng/ai-data-science-team-w/blob/main/Tool%20V3/docs/INSIGHT_QUALITY_REGRESSION.md).
- **Docs index:** [README.md](https://github.com/is443-eng/ai-data-science-team-w/blob/main/Tool%20V3/docs/README.md), [submission_notes.md](https://github.com/is443-eng/ai-data-science-team-w/blob/main/Tool%20V3/docs/submission_notes.md), [DEPLOYMENT_TEST_LOG.md](https://github.com/is443-eng/ai-data-science-team-w/blob/main/Tool%20V3/docs/DEPLOYMENT_TEST_LOG.md), [APP_SUBMISSION_READINESS.md](https://github.com/is443-eng/ai-data-science-team-w/blob/main/Tool%20V3/docs/APP_SUBMISSION_READINESS.md), [MANUAL_QA_CHECKLIST.md](https://github.com/is443-eng/ai-data-science-team-w/blob/main/Tool%20V3/docs/MANUAL_QA_CHECKLIST.md).

---

← [Back to docs index (README)](https://github.com/is443-eng/ai-data-science-team-w/blob/main/Tool%20V3/docs/README.md)