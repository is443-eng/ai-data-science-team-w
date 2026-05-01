# App V2 documentation

Documentation for **Tool V2** submission and maintenance.

## Four submission write-ups (export / attach as required)

| Document | Covers |
|----------|--------|
| [**SYSTEM_ARCHITECTURE.md**](SYSTEM_ARCHITECTURE.md) | Agent roles, workflow, component interaction (+ pointer to Mermaid diagram) |
| [**TOOLS_IMPLEMENTATION.md**](TOOLS_IMPLEMENTATION.md) | Tool functions: names, purpose, parameters, returns (CDC tools; not vector RAG) |
| [**TECHNICAL_DETAILS.md**](TECHNICAL_DETAILS.md) | API keys, endpoints, packages, file structure, deployment platform |
| [**USAGE_INSTRUCTIONS.md**](USAGE_INSTRUCTIONS.md) | How to use the deployed app; password / access note |

## Submission package (course deliverable)

| Document | Purpose |
|----------|---------|
| [**TOOL2_SUBMISSION_PACKAGE.md**](TOOL2_SUBMISSION_PACKAGE.md) | Main narrative for Canvas / Word export; links table, team roles, pointers for grading |
| [**submission_notes.md**](submission_notes.md) | Live URL, deploy commands, smoke tests, API keys |
| [**APP_SUBMISSION_READINESS.md**](APP_SUBMISSION_READINESS.md) | Pre-freeze checklist (pytest, QA, deploy) |
| [**DEPLOYMENT_TEST_LOG.md**](DEPLOYMENT_TEST_LOG.md) | Step-by-step deploy verification |
| [**MANUAL_QA_CHECKLIST.md**](MANUAL_QA_CHECKLIST.md) | Browser QA after changes |

## Technical reference

| Document | Purpose |
|----------|---------|
| [**ARCHITECTURE.md**](ARCHITECTURE.md) | System flow, **five-agent** orchestration, Mermaid diagram, state risk + baseline notes |
| [**diagrams/architecture.mmd**](diagrams/architecture.mmd) | Same diagram for export (docx, PNG) |
| [**INTERFACE_CONTRACTS.md**](INTERFACE_CONTRACTS.md) | `ToolOutput`, `AgentContext`, `AgentResult`, registry names |

## Planning (historical / scope)

| Path | Notes |
|------|--------|
| [planning/](planning/) | Segmented build plan, TOOL2 rubric, scope notes |

## Workflow

1. Deploy and test → fill **`submission_notes.md`** with the live URL.  
2. Complete **`DEPLOYMENT_TEST_LOG.md`** and **`MANUAL_QA_CHECKLIST.md`**.  
3. Run **`APP_SUBMISSION_READINESS.md`** checks.  
4. Finalize **`TOOL2_SUBMISSION_PACKAGE.md`** and export to **`.docx`** if required.
