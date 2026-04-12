# App submission readiness (Tool V2)

Use this checklist when you are ready to **freeze** the app before finalizing the TOOL2 documentation package. Order: **deploy testing** ([`DEPLOYMENT_TEST_LOG.md`](DEPLOYMENT_TEST_LOG.md)) → **this checklist** → **finalize** [`TOOL2_SUBMISSION_PACKAGE.md`](TOOL2_SUBMISSION_PACKAGE.md).

## Automated tests

From `Tool V2/`:

```bash
python3 -m pytest tests/ -q
```

- [ ] Full suite passes (use network if you run live parity tests against CDC).

## Manual QA

- [ ] Complete [`MANUAL_QA_CHECKLIST.md`](MANUAL_QA_CHECKLIST.md) for the build you intend to submit (local `streamlit run app.py` and/or live Connect URL).

## Agents and data

- [ ] **Overview:** Agent insights load with `OLLAMA_API_KEY` set, or show a clear message when the key is missing.
- [ ] **State:** Changing the sidebar state updates state-scoped narratives when tool rows match (see orchestrator behavior in [`../agents/orchestrator.py`](../agents/orchestrator.py)).

## Deployment

- [ ] Real Connect deploy succeeded and **live URL** is recorded in [`submission_notes.md`](submission_notes.md).

## Documentation (pointer only)

Final docx / Canvas narrative is **last** — see [`TOOL2_SUBMISSION_PACKAGE.md`](TOOL2_SUBMISSION_PACKAGE.md) after the items above are satisfied.
