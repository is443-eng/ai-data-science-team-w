# TOOL3 — App V3 submission package (source for .docx)

**Course reference:** [TOOL3.md](TOOL3.md) (rubric, 100 pts). This package is the **main written deliverable** to export to `**.docx`** for Canvas, together with links to the repo, **working** live app, and presentation materials.

**Canvas single .docx (per TOOL3.md “To Submit”):** Include (1) link to this **GitHub repo main page**, (2) link to the **live app**, (3) link to **presentation materials** (demo script / slides / video). Make it obvious where each **rubric item** is answered: use the **Links** and **Rubric mapping** sections below; deeper evidence lives in-repo under `Tool V3/docs/` (QC/regression, deployment verification, architecture).

**When to treat as final:** After [DEPLOYMENT_TEST_LOG.md](DEPLOYMENT_TEST_LOG.md) is complete, the app is **deployed and verified**, and [APP_SUBMISSION_READINESS.md](APP_SUBMISSION_READINESS.md) checks are satisfied.

**Export:** A Word file may be generated as `**TOOL3_SUBMISSION.docx`** (add the architecture diagram and confirm team table before submit). Example: `pandoc TOOL3_SUBMISSION_PACKAGE.md -o TOOL3_SUBMISSION.docx`. Include a **rendered image** of the process diagram from [ARCHITECTURE.md](ARCHITECTURE.md) (Mermaid) or [diagrams/architecture.mmd](diagrams/architecture.mmd).

**Final links table:** Must match [submission_notes.md](submission_notes.md).

---

## Links (required)


| Item                                          | URL                                                                                                                                                              |
| --------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| GitHub repository (main branch)               | [https://github.com/is443-eng/ai-data-science-team-w](https://github.com/is443-eng/ai-data-science-team-w)                                                       |
| Live deployed app (Posit Connect)             | [https://connect.systems-apps.com/content/b8cfc1fa-8eb0-4c2e-ba98-b5f06837e933/](https://connect.systems-apps.com/content/b8cfc1fa-8eb0-4c2e-ba98-b5f06837e933/) |
| Presentation materials (demo script / slides) | [Demo Script Talking Points.md](Demo%20Script%20Talking%20Points.md) (and any slide deck or video link your team adds in Canvas)                                 |


---

## Rubric mapping (TOOL3 — 100 pts)


| Rubric item (from TOOL3)                     | How the shipped app addresses it                                                                                                                                                                                                                      |
| -------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **50 pts — Production-ready functional app** |                                                                                                                                                                                                                                                       |
| Stakeholder alignment (10)                   | Public-health–oriented **Measles** dashboard: CDC open data, plain-language **Overview**, **state/national** insights, risk tiers and forecast context—not clinical advice; disclaimer in-app.                                                        |
| Clarity (10)                                 | Streamlit **sidebar** navigation, **Data as of** and per-source load lines, **Overview** baseline + **Insights** with optional state; expanders for methodology.                                                                                      |
| Streamlining (10)                            | Focused tab set (Overview, Historical, Kindergarten, Wastewater vs NNDSS, State risk, Forecast); LLM optional via **Include AI-written summaries**; no duplicate product surfaces.                                                                    |
| Efficiency (10)                              | **1-hour** CDC/tool fetch caching, **session reuse** of model outputs within TTL, **Generate insights** reuses cached Socrata rows when available; **Python 3.12.4** on Connect.                                                                      |
| Reliability (10)                             | **57** automated tests (`Tool V3/tests/`); partial tool/LLM failure handling in orchestrator; graceful empty states; **tornado** and explicit **scipy** in `requirements.txt` for Connect builds.                                                    |
| **20 pts — Quality control and validation**  |                                                                                                                                                                                                                                                       |
| QC implementation (10)                       | **Insight quality rubric** (`INSIGHT_QC_ENABLED=1`) scores national/state summaries; **refinement loop** (`INSIGHT_REFINEMENT_*`) with documented env vars.                                                                                           |
| Evidence of AI performance (10)              | **Insight quality expander** on Overview when QC runs; **insight regression** tests ([INSIGHT_QUALITY_REGRESSION.md](INSIGHT_QUALITY_REGRESSION.md)); `InsightQCResult` in [INTERFACE_CONTRACTS.md](INTERFACE_CONTRACTS.md) / `contracts/schemas.py`. |
| **20 pts — Presentation**                    |                                                                                                                                                                                                                                                       |
| Live demonstration (10)                      | **Demo Script Talking Points** supports a 3–5 minute walkthrough of the **deployed** URL above.                                                                                                                                                       |
| Presentation materials (10)                  | Demo script + (team provides slides or video per course / DL policy in Canvas).                                                                                                                                                                       |
| **10 pts — Deployed app link**               | **Working** Posit Connect URL in the table: direct content link above; Connect dashboard: `https://connect.systems-apps.com/connect/#/apps/b8cfc1fa-8eb0-4c2e-ba98-b5f06837e933`                                                                      |
| **Agentic loop** (course overview; design yours) | After tools run, **five LLM stages**: Agent **1** (tool runner) → **2 ∥ 3** (state vs national analysts) → **4 ∥ 5** (state vs national reporters). Optional **insight QC / refinement** env toggles. See [ARCHITECTURE.md](ARCHITECTURE.md), `agents/orchestrator.py`. |

---

## Description (3–5 paragraphs)

**Predictive Measles Risk Dashboard — Tool V3** is a **Streamlit** application for public health stakeholders and residents to explore **measles-related risk signals** in the United States using **CDC open data**. The app loads kindergarten MMR coverage, wastewater surveillance, NNDSS case lines, and child/teen coverage tools, then applies a **statistical risk model** (stage-1 alarm, forecast inputs, **state composite** scores and tiers) and an **Overview baseline gauge** aligned with historical and current-season national surveillance.

**Agentic orchestration (five LLM steps after tools):** **Agent 1** runs a fixed pipeline of CDC-backed **tools** through `tools/registry.py`. **Agents 2 and 3** run **in parallel** (state vs national analyst), with **OpenAI function calling** when `OPENAI_API_KEY` is set. **Agents 4 and 5** run **in parallel** next: state and **national** reporter prose. Outputs appear under **Overview → Insights** after **Generate insights** (national-only or national + state). Optional **insight QC** and **refinement** env toggles support course **quality control** requirements. The design grounds narrative in tool outputs, dashboard metrics, and precomputed state-risk JSON from the same run.

**APIs and services:** CDC Socrata (optional `SOCRATA_APP_TOKEN`), **OpenAI** Chat Completions (preferred for agents) or **Ollama Cloud** as fallback. **Deployment:** **Posit Connect** (Cornell Systems Engineering Connect) with `deployment/deploy_me.py`, Python **3.12.4**, runtime secrets forwarded via `rsconnect` `**-E`**.

**Repository root for the app:** `Tool V3/` (not to be confused with historical `Tool V2` documentation paths in older notes). All technical documentation for instructors is under `Tool V3/docs/`.

---

## Process diagram

Embed the diagram from [ARCHITECTURE.md](ARCHITECTURE.md) (Mermaid) or export [diagrams/architecture.mmd](diagrams/architecture.mmd) to PNG/SVG for the **.docx**.

---

## Technical documentation

### System architecture

- **Frontend:** Streamlit (`app.py`); **Overview** integrates `ui/agent_insights.py` (**Generate insights**).
- **Data:** `loaders.py` + `tools/*` for CDC; `risk.py` for alarm model, aggregates, **state composite** (`get_state_risk_df`), baseline, forecast.
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


Exact fields: [INTERFACE_CONTRACTS.md](INTERFACE_CONTRACTS.md).

### Technical details

- **Python:** `Tool V3/requirements.txt` (includes **streamlit**, **tornado** for Connect runtime, **scipy** for `risk.py`, **scikit-learn**, etc.); bundle targets **Python 3.12.4**; `[.python-version](../.python-version)` and `deployment/deploy_me.py` defaults align with the Connect image.
- **Secrets:** `OPENAI_API_KEY` (recommended), `OLLAMA_API_KEY` (fallback), optional `SOCRATA_APP_TOKEN`, `OPENAI_MODEL`; deploy keys (`POSIT_PUBLISHER_KEY`, etc.) only on the **publisher** machine — use Connect **Vars** and `deploy_me.py` `**-E`** forwarding. Never commit secrets.
- **Repo layout:** `Tool V3/` is the app root: `contracts/`, `tools/`, `agents/`, `prompts/`, `ui/`, `tests/`, `docs/`, `deployment/`.

### Usage instructions (deployed app)

1. Open the **live URL** (see Links table).
2. Use **Refresh data** in the sidebar to bypass cache and pull fresh CDC data when needed.
3. On **Overview**, optional **State (optional)** and **Generate insights** (requires server LLM keys unless AI summaries are off).
4. Use other tabs for charts, maps, and forecast; see [USAGE_INSTRUCTIONS.md](USAGE_INSTRUCTIONS.md).

*Password:* not required unless the team adds optional auth (document in submission if added).

---

## Team members by role


| Name             | Role (examples)                                                     |
| ---------------- | ------------------------------------------------------------------- |
| Jonathan Lloyd | Frontend and Deployment |
| Ian Steigmeyer  | Backend and Agents |


---

## Pointers for grading

- **Orchestration + tools:** `agents/orchestrator.py`, `tools/registry.py`, `tests/test_orchestrator.py`.
- **UI:** `app.py`, `ui/agent_insights.py`.
- **Risk + state table:** `risk.py`, `tests/test_risk_leaderboard.py`.
- **QC / regression:** `agents/insight_quality.py`, `tests/test_insight_quality.py`, [INSIGHT_QUALITY_REGRESSION.md](INSIGHT_QUALITY_REGRESSION.md).
- **Docs index:** [README.md](README.md), [submission_notes.md](submission_notes.md), [DEPLOYMENT_TEST_LOG.md](DEPLOYMENT_TEST_LOG.md), [APP_SUBMISSION_READINESS.md](APP_SUBMISSION_READINESS.md), [MANUAL_QA_CHECKLIST.md](MANUAL_QA_CHECKLIST.md).

---

← [Back to docs index](README.md)