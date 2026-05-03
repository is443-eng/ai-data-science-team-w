# App submission readiness (Tool V3)

Use this checklist when you are ready to **freeze** the app before finalizing the V3 documentation package.
Recommended order: **deploy testing** ([`DEPLOYMENT_TEST_LOG.md`](DEPLOYMENT_TEST_LOG.md)) → **this checklist** → **finalize** [`TOOL3_SUBMISSION_PACKAGE.md`](TOOL3_SUBMISSION_PACKAGE.md) (see [`TOOL3.md`](TOOL3.md) rubric).

## Collaboration plan

- [ ] For ian/jonathan ownership, handoff criteria, and collaboration rhythm, use [`planning/final_weekend_handoff_plan.md`](planning/final_weekend_handoff_plan.md).

## Automated tests

From repo root (or target the Tool V3 tests directly):

```bash
python3 -m pytest "Tool V3/tests/" -q
```

- [ ] Full suite passes (use network if you run live parity tests against CDC).
- [ ] Insight quality and loop tests pass in particular (`test_insight_quality.py`, `test_insight_regression.py`, `test_orchestrator.py`).

## Manual QA

- [ ] Complete [`MANUAL_QA_CHECKLIST.md`](MANUAL_QA_CHECKLIST.md) for the build you intend to submit (local `streamlit run app.py` and/or live Connect URL).

## Agents, quality, and loop behavior

- [ ] **Overview → Insights:** **Generate insights** completes; with `OPENAI_API_KEY` or `OLLAMA_API_KEY`, national summary (Agent 5) renders; with a state selected, state summary (Agent 4) renders; or a clear error when keys are missing.
- [ ] **State:** Changing **State (optional)** and re-running updates state-scoped content when tool rows match (see [`../agents/orchestrator.py`](../agents/orchestrator.py)).
- [ ] **Insight QC (optional):** with `INSIGHT_QC_ENABLED=1`, the **Insight quality rubric** expander appears and shows scored results for national/state summaries when available.
- [ ] **Refinement loop (optional):** with `INSIGHT_REFINEMENT_ENABLED=1` and QC on, summaries still render normally and include refinement warnings/round metadata in the run output when applicable.
- [ ] **National-only mode:** with no selected state, Agent 3/5 path still works and does not regress when QC/refinement toggles are on.

## Environment configuration

- [ ] Runtime environment is finalized and recorded: `SOCRATA_APP_TOKEN`, one LLM path (`OPENAI_API_KEY` and optional `OPENAI_MODEL` or `OLLAMA_API_KEY`), and quality/loop toggles (`INSIGHT_QC_*`, `INSIGHT_REFINEMENT_*`) as intended for release.

## Deployment

- [ ] Real Connect deploy succeeded and **live URL** is recorded in [`submission_notes.md`](submission_notes.md).

## Documentation sync (post-deploy-ready)

- [x] Update [`TECHNICAL_DETAILS.md`](TECHNICAL_DETAILS.md) with final quality/loop env var defaults and deployment notes.
- [x] Update [`INTERFACE_CONTRACTS.md`](INTERFACE_CONTRACTS.md) to reflect `InsightQCResult` and `OrchestratorRun.insight_quality`.
- [x] Update [`USAGE_INSTRUCTIONS.md`](USAGE_INSTRUCTIONS.md) and [`MANUAL_QA_CHECKLIST.md`](MANUAL_QA_CHECKLIST.md) for quality/loop UX and validation steps.
- [x] Verify docs index links in [`README.md`](README.md) include all new quality/regression docs and remain accurate.

Final docx / Canvas narrative is **last** — complete after all checks above pass.
