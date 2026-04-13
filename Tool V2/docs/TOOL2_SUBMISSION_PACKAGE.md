# TOOL2 — App V2 submission package (source for .docx)

**When to treat this as final:** After **deployment testing** ([`DEPLOYMENT_TEST_LOG.md`](DEPLOYMENT_TEST_LOG.md)), a working **live URL** in [`submission_notes.md`](submission_notes.md), and [`APP_SUBMISSION_READINESS.md`](APP_SUBMISSION_READINESS.md) checks. Do not freeze the written package until the shipped app matches what you describe.

**Instructions:** A generated Word file may exist alongside this markdown as **`TOOL2_SUBMISSION.docx`** (plain export of this content—add the diagram image and team links before submitting). You can also copy sections manually, or export with Pandoc: `pandoc TOOL2_SUBMISSION_PACKAGE.md -o TOOL2_SUBMISSION.docx`.

Include a **rendered image** of the process diagram (from [`ARCHITECTURE.md`](ARCHITECTURE.md) Mermaid or [`diagrams/architecture.mmd`](diagrams/architecture.mmd)) in the docx.

**Final links table:** Copy the same GitHub and app URLs you recorded in [`submission_notes.md`](submission_notes.md) into the table below.

---

## Links (required)

| Item | URL |
|------|-----|
| GitHub repository (main branch) | _Your team URL_ |
| Live deployed app (Posit Connect or similar) | _Your app URL_ |

---

## Description (3–5 paragraphs)

**Predictive Measles Risk Dashboard — Tool V2** is a Streamlit application that helps public health stakeholders and concerned residents understand measles-related risk signals in the United States using CDC open data. The app loads kindergarten immunization coverage, wastewater surveillance proxies, and NNDSS case data, then applies a statistical risk model to produce alarm probabilities, **state-level composite scores and tiers**, short-term outlook text, and an **Overview baseline gauge** aligned with historical and current-season national surveillance.

**Agentic orchestration (five LLM steps after tools):** **Agent 1** runs a fixed pipeline of CDC-backed **tools** (immunization and surveillance data pulls) through a central registry. **Agents 2 and 3** run **in parallel** (state analyst vs national analyst), optionally using **OpenAI function calling** when configured. **Agents 4 and 5** run **in parallel** next: **Agent 4** produces a readable **state summary** from Agent 2; **Agent 5** produces the **national narrative** from Agent 3, including top states by composite risk when data is available. Outputs appear under **Overview → Insights** after **Generate insights** (national-only or national + state when a state is selected). The design reduces hallucinated numbers by grounding prose in tool outputs, dashboard metrics, and precomputed state-risk JSON.

**Tool calling** satisfies the course requirement: each tool wraps a real data access or transformation path (Socrata queries and aligned schemas) and returns structured results consumed by agents and the UI. **Stakeholder value:** staff get reproducible tool-backed summaries; families get clearer language tied to the same underlying data.

**APIs and services:** CDC Socrata endpoints (with optional app token), **OpenAI** Chat Completions (preferred for agent tool calls) or **Ollama Cloud** when OpenAI is not set. **Deployment:** Posit Connect (or compatible host) so the app stays publicly reachable, consistent with course expectations.

---

## Process diagram

Embed the diagram from [`ARCHITECTURE.md`](ARCHITECTURE.md) (Mermaid) or export [`diagrams/architecture.mmd`](diagrams/architecture.mmd) to PNG/SVG for this section.

---

## Technical documentation

### System architecture

- **Frontend:** Streamlit (`app.py`), multi-page navigation via radio control; Overview integrates `ui/agent_insights.py` for orchestrator results (**Generate insights**).
- **Data:** `loaders/` fetch and normalize CDC datasets; `risk/` fits the alarm model, national aggregates, **state composite risk** (`get_state_risk_df`), baseline gauge, and harmonization notes where applicable.
- **Orchestration:** `agents/orchestrator.py` — Agent 1 (tools) → Agents 2 ∥ 3 (LLM) → Agents 4 ∥ 5 (LLM). State-filtered excerpts from tool `records` ensure state narratives change when the user changes state. **Agent 1** payloads are used to rebuild **state_risk_records_json** for agents when possible so rankings match the same run’s CDC data.
- **Prompts:** `prompts/*.md` + `prompts/loader.py`; shared guardrails discourage invented statistics; national prompts constrain structure (e.g. five-sentence national paragraph with top states embedded per `agent_5_national_reporter.md`).

### Tool functions (names and purpose)

| Tool name | Purpose | Returns (conceptually) |
|-----------|---------|-------------------------|
| `child_vax` | Child/adolescent vaccination coverage context | Rows + metadata per contracts |
| `kindergarten_vax` | Kindergarten MMR coverage | Rows + metadata |
| `teen_vax` | Teen vaccination series | Rows + metadata |
| `wastewater` | Wastewater / surveillance signals | Rows + metadata |
| `nndss` | NNDSS case line lists | Rows + metadata |

Exact fields and statuses are defined in [`INTERFACE_CONTRACTS.md`](INTERFACE_CONTRACTS.md).

### Technical details

- **Python:** see `requirements.txt`; deployment bundle targets Python 3.12 (`deployment/deploy_me.py`).
- **Secrets:** `OPENAI_API_KEY` (recommended for agents), `OLLAMA_API_KEY` (fallback), optional `SOCRATA_APP_TOKEN`, Connect keys for deploy — never committed; use `.env` locally and Connect `-E` forwarding as documented in `deployment/deploy_me.py`.
- **Repo layout:** `Tool V2/` is the app root; `contracts/`, `tools/`, `agents/`, `prompts/`, `ui/`, `tests/`, `docs/`.

### Usage instructions (deployed app)

1. Open the live URL (see Links table).
2. Use **Refresh data** in the sidebar after changing environment or for a clean pull.
3. On **Overview**, set optional **Insights** options, then **Generate insights** for tool-backed summaries (requires `OPENAI_API_KEY` or `OLLAMA_API_KEY` on the server unless LLM is disabled).
4. Use other tabs for charts, maps, and forecast tables; choose **National only** or a **state** in Insights for tailored output.

_Password:_ not required unless your team adds optional auth (if added, document the password for the instructor here).

---

## Team members by role

| Name | Role (examples) |
|------|-------------------|
| _Name_ | _e.g. Backend / API, Frontend, Agent orchestration, QA, Deployment_ |
| _Name_ | _…_ |

---

## Pointers for grading

- **Orchestration + tools:** `agents/orchestrator.py`, `tools/registry.py`, `tests/test_orchestrator.py`.
- **UI integration:** `app.py` (Overview), `ui/agent_insights.py`.
- **Risk + state table:** `risk.py` (`get_state_risk_df`, baseline harmonization), `tests/test_risk_leaderboard.py`.
- **Docs:** `docs/ARCHITECTURE.md`, `docs/INTERFACE_CONTRACTS.md`, `docs/submission_notes.md`, `docs/DEPLOYMENT_TEST_LOG.md`, `docs/APP_SUBMISSION_READINESS.md`, `docs/MANUAL_QA_CHECKLIST.md`.
