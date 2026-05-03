# Tool V3 documentation

Documentation for **Tool V3** (App V3 / production-ready assignment) and instructor grading.

## Assignment rubric

| Document | Purpose |
|----------|---------|
| [**TOOL3.md**](TOOL3.md) | Official course tool brief (100 pt rubric: production-ready app, QC, presentation, **working deployed link**). Course text may say **ShinyApp**; this project is **Streamlit** on Posit Connect—same deliverable type (hosted interactive dashboard). |

**Private data / passwords:** If you ever use restricted data, TOOL3 expects optional password protection and the password listed in submission; this build uses **public CDC data** only—see [USAGE_INSTRUCTIONS.md](USAGE_INSTRUCTIONS.md).

## Four technical write-ups

| Document | Covers |
|----------|--------|
| [**SYSTEM_ARCHITECTURE.md**](SYSTEM_ARCHITECTURE.md) | Agent roles, workflow, component interaction (+ pointer to Mermaid diagram) |
| [**TOOLS_IMPLEMENTATION.md**](TOOLS_IMPLEMENTATION.md) | Tool functions: names, purpose, parameters, returns (CDC tools) |
| [**TECHNICAL_DETAILS.md**](TECHNICAL_DETAILS.md) | API keys, endpoints, packages, file structure, deployment platform |
| [**USAGE_INSTRUCTIONS.md**](USAGE_INSTRUCTIONS.md) | How to use the **deployed** app; access note |

## Submission package (course deliverable)

| Document | Purpose |
|----------|---------|
| [**TOOL3_SUBMISSION_PACKAGE.md**](TOOL3_SUBMISSION_PACKAGE.md) | Main narrative for Canvas / Word export; links table, rubric mapping, team roles, pointers for grading |
| [**submission_notes.md**](submission_notes.md) | **Live URL**, deploy commands, smoke tests, API keys |
| [**APP_SUBMISSION_READINESS.md**](APP_SUBMISSION_READINESS.md) | Pre-freeze checklist (pytest, QA, deploy) |
| [**DEPLOYMENT_TEST_LOG.md**](DEPLOYMENT_TEST_LOG.md) | Step-by-step deploy verification |
| [**MANUAL_QA_CHECKLIST.md**](MANUAL_QA_CHECKLIST.md) | Browser QA after changes |

## Presentation / demo

| Document | Purpose |
|----------|---------|
| [**Demo Script Talking Points.md**](Demo%20Script%20Talking%20Points.md) | Live demo script for instructor session or video |

## Technical reference

| Document | Purpose |
|----------|---------|
| [**ARCHITECTURE.md**](ARCHITECTURE.md) | System flow, **five-agent** orchestration, Mermaid diagram, state risk + baseline notes |
| [**diagrams/architecture.mmd**](diagrams/architecture.mmd) | Same diagram for export (docx, PNG) |
| [**INTERFACE_CONTRACTS.md**](INTERFACE_CONTRACTS.md) | `ToolOutput`, `AgentContext`, `AgentResult`, **`InsightQCResult`**, registry names |
| [**INSIGHT_QUALITY_REGRESSION.md**](INSIGHT_QUALITY_REGRESSION.md) | Manual smoke checks + prompt score comparison workflow |

## Planning (historical / scope)

| Path | Notes |
|------|--------|
| [planning/](planning/) | Handoff and dev notes |

## Workflow

1. Deploy and test → fill **`submission_notes.md`** with the live URL.
2. Complete **`DEPLOYMENT_TEST_LOG.md`** and **`MANUAL_QA_CHECKLIST.md`**.
3. Run **`APP_SUBMISSION_READINESS.md`** checks.
4. Finalize **`TOOL3_SUBMISSION_PACKAGE.md`** and export to **`.docx`** if required — include **GitHub**, **live app**, and **presentation** links per **TOOL3.md** “To Submit”.
