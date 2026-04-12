# Submission notes (Segment 6–7)

**Workflow:** Test deployment and record a working URL **before** treating the TOOL2 doc package as final. See [`DEPLOYMENT_TEST_LOG.md`](DEPLOYMENT_TEST_LOG.md) for a step-by-step checklist.

## Repository

- **GitHub (main):** _Add your team’s public repo URL here._

## Deployed app (Posit Connect)

- **Live app URL:** _Paste the Connect content URL after a successful deploy — e.g. `https://connect.systems-apps.com/.../`_
- **Deploy command (from `Tool V2/`):**  
  `python3 deployment/deploy_me.py`  
  Set `CONNECT_API_KEY` (or `POSIT_PUBLISHER_KEY` / `RSCONNECT_API_KEY`) and optionally `SOCRATA_APP_TOKEN`, `OLLAMA_API_KEY` in `.env` so the bundle forwards API access to Connect (`-E` flags in script).
- **Dry-run (validates bundle args without publishing):**  
  `python3 deployment/deploy_me.py --dry-run`  
  Verified: exits `0`, prints `rsconnect` command and `Tool V2` working directory (no Connect key required). Full deploy requires a key in `.env` or `--api-key`.
- **Optional HTTP smoke check:**  
  `bash deployment/smoke_check_url.sh '<your live URL>'`

## Smoke test (after URL exists)

1. Open the live URL; confirm the Streamlit app loads (title **Risk of Measles Outbreak in US**).
2. Sidebar **Refresh data** — no hard crash; data/captions or clear load messages.
3. **Overview** — metrics and agent insights section (or graceful LLM-off message).
4. Spot-check one other tab (e.g. **Historical trends** or **Forecast**).

Full manual pass: [`MANUAL_QA_CHECKLIST.md`](MANUAL_QA_CHECKLIST.md).

## Documentation for instructors

- Deployment checklist: [`DEPLOYMENT_TEST_LOG.md`](DEPLOYMENT_TEST_LOG.md).
- App readiness before final docs: [`APP_SUBMISSION_READINESS.md`](APP_SUBMISSION_READINESS.md).
- Architecture and workflow: [`ARCHITECTURE.md`](ARCHITECTURE.md) (includes process diagram source).
- Tool registry / contracts: [`INTERFACE_CONTRACTS.md`](INTERFACE_CONTRACTS.md), [`../tools/`](../tools/) modules.
- TOOL2 written deliverable (export to **.docx** for Canvas, **after** URL + app freeze): [`TOOL2_SUBMISSION_PACKAGE.md`](TOOL2_SUBMISSION_PACKAGE.md).
