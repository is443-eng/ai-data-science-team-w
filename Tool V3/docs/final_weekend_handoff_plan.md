# Final weekend handoff plan

Use this split to reduce blocking while preserving final release order.

## Owners

### ian (Person A): agents + feature behavior

- Own implementation/stability for orchestrator and insight generation paths, including national/state behavior and state-scoped updates (see [`../agents/orchestrator.py`](../agents/orchestrator.py)).
- Own **Insight QC** behavior behind `INSIGHT_QC_ENABLED=1`.
- Own **Refinement loop** behavior behind `INSIGHT_REFINEMENT_ENABLED=1` (including warning/round metadata when applicable).
- Keep feature tests green, especially `test_insight_quality.py`, `test_insight_regression.py`, and `test_orchestrator.py`.
- Hand off a stable build for final end-to-end QA and doc lock.

### jonathan (Person B): QA + release validation + docs sync

- Run and maintain [`MANUAL_QA_CHECKLIST.md`](MANUAL_QA_CHECKLIST.md) against the target build (local and/or live URL).
- Validate deployment readiness and record the live URL in [`submission_notes.md`](submission_notes.md).
- Verify environment variable decisions for release (`SOCRATA_APP_TOKEN`, LLM path, `INSIGHT_QC_*`, `INSIGHT_REFINEMENT_*`).
- Prepare and finalize docs sync updates in:
  - [`TECHNICAL_DETAILS.md`](TECHNICAL_DETAILS.md)
  - [`INTERFACE_CONTRACTS.md`](INTERFACE_CONTRACTS.md)
  - [`USAGE_INSTRUCTIONS.md`](USAGE_INSTRUCTIONS.md)
  - [`MANUAL_QA_CHECKLIST.md`](MANUAL_QA_CHECKLIST.md)
  - [`README.md`](README.md)
- Run final submission pass after ian's feature handoff to confirm no regressions with QC/refinement toggles enabled.

## Coordination checkpoints

- Work can happen in parallel, but **final QA sign-off** should occur after ian's QC/refinement behavior is stabilized.
- Before freeze, both confirm: automated tests pass, manual QA passes, and docs reflect final runtime defaults.

## Handoff checklist (ian ↔ jonathan)

Use this sequence every cycle (not just at the end) so each handoff has clear entry/exit criteria.

### 1) ian -> jonathan: feature-ready handoff

**Done (ian, 2026-05-02):** feature scope is on `FEATURE_READY_HANDOFF_1` and pushed to `origin`; local `python3 -m pytest tests/ -q` is green (live Socrata parity tests may skip without `SOCRATA_APP_TOKEN` or when CDC/Socrata is unavailable). Orchestrator unit tests pin `INSIGHT_REFINEMENT_ENABLED=0` and `INSIGHT_QC_ENABLED=0` for determinism; enable toggles for QA per env/`TECHNICAL_DETAILS.md`. No known blockers for Jonathan’s QA pass beyond upstream API availability for optional live parity tests.

ian marks handoff ready only when all are true:

- [x] Relevant feature scope is merged/in branch and runnable locally.
- [x] `python3 -m pytest "Tool V3/tests/" -q` passes locally (or targeted failures are documented and approved).
- [x] For the changed scope, `test_insight_quality.py`, `test_insight_regression.py`, and `test_orchestrator.py` are green.
- [x] Behavior notes are posted with exact toggle settings used (`INSIGHT_QC_ENABLED`, `INSIGHT_REFINEMENT_ENABLED`, model path).
- [x] Known limitations/regressions (if any) are explicitly listed with expected QA impact.

### 2) jonathan QA pass: validation + feedback handoff

jonathan validates and returns one of two outcomes: **Pass** or **Needs fixes**.

- [ ] Run [`MANUAL_QA_CHECKLIST.md`](MANUAL_QA_CHECKLIST.md) against the same toggle settings ian reported.
- [ ] Confirm Overview -> Insights works in both national-only and state-selected modes.
- [ ] Confirm QC/refinement UX and metadata behavior match checklist expectations.
- [ ] Record reproducible issues with: steps, expected vs actual, env/toggles, and screenshots/logs if helpful.
- [ ] Send a short QA result note: **Pass** (ready for deploy/doc sync) or **Needs fixes** (returns to ian with issue list).

### 3) ian fix loop (only if QA finds issues)

- [ ] Triage QA issues into: blocker, must-fix, can-defer.
- [ ] Fix blockers/must-fix items and rerun tests.
- [ ] Re-handoff to jonathan with updated behavior notes and commit references.

### 4) release-close handoff (joint)

Complete only after QA result is **Pass**:

- [ ] jonathan updates docs/env/deploy notes (`TECHNICAL_DETAILS.md`, `INTERFACE_CONTRACTS.md`, `USAGE_INSTRUCTIONS.md`, `README.md`, `submission_notes.md`).
- [ ] ian verifies technical accuracy of docs for QC/refinement/orchestrator behavior.
- [ ] Both do final readiness sweep in [`APP_SUBMISSION_READINESS.md`](APP_SUBMISSION_READINESS.md) before freeze.

## Suggested collaboration rhythm

- Daily 10-15 minute sync: current scope, blockers, handoff target time.
- One active owner per issue at a time (avoid duplicate debugging).
- Keep a single shared handoff note template to reduce ambiguity.
