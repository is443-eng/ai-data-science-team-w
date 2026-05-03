# Submission notes (Tool V3)

**Workflow:** Test deployment and record a working URL **before** treating the **TOOL3** doc package as final. See [DEPLOYMENT_TEST_LOG.md](DEPLOYMENT_TEST_LOG.md) for a step-by-step checklist.

## Repository

- **GitHub (main):** https://github.com/is443-eng/ai-data-science-team-w

## Presentation materials (TOOL3 .docx)

- **Written demo script:** [Demo Script Talking Points.md](Demo%20Script%20Talking%20Points.md) (same topic as live demo / optional video).
- Add slide deck or hosted video links your section requires; keep them mirrored in [TOOL3_SUBMISSION_PACKAGE.md](TOOL3_SUBMISSION_PACKAGE.md) when you freeze the submission package.

## Deployed app (Posit Connect)

- **Live app (direct):** https://connect.systems-apps.com/content/b8cfc1fa-8eb0-4c2e-ba98-b5f06837e933/
- **Connect dashboard (logs / settings):** https://connect.systems-apps.com/connect/#/apps/b8cfc1fa-8eb0-4c2e-ba98-b5f06837e933
- **Status (2026-05):** App **operational** on Connect after bundle includes **tornado** (Posit Streamlit runtime) and **Python 3.12.4** environment match.
- **Deploy / update (from `Tool V3/`):**  
  `python deployment/deploy_me.py --app-id b8cfc1fa-8eb0-4c2e-ba98-b5f06837e933`  
  Or new content: `python deployment/deploy_me.py`  
  Set `CONNECT_API_KEY` or **`POSIT_PUBLISHER_KEY`** (or other publisher keys) and optionally `SOCRATA_APP_TOKEN`, `OLLAMA_API_KEY`, **`OPENAI_API_KEY`** (and optional `OPENAI_MODEL`) in `.env` so the script can forward runtime access to Connect (`-E`). Prefer **OpenAI** for agent tool-calling when `OPENAI_API_KEY` is set; otherwise **Ollama Cloud** if `OLLAMA_API_KEY` is set.
- **Dry-run:**  
  `python deployment/deploy_me.py --dry-run`  
  Exits `0`, prints the `rsconnect` command; working directory is **`Tool V3`**. No Connect key required for dry-run.
- **Post-deploy verify:** If `rsconnect` post-check fails, use `--no-verify` and confirm the app in the browser; see [deployment/README.md](../deployment/README.md).

## Smoke test (after URL exists)

1. Open the **direct** live URL; confirm the Streamlit app loads (title **Risk of Measles Outbreak in US**).
2. Sidebar **Refresh data** — no hard crash; **data as of** and source captions sensible.
3. **Overview** — baseline gauge and **Insights** (or clear messaging if LLM keys missing).
4. Spot-check one other tab (e.g. **Historical trends** or **Forecast**).

Full manual pass: [MANUAL_QA_CHECKLIST.md](MANUAL_QA_CHECKLIST.md).

## Documentation for instructors

- **Index:** [README.md](README.md) (this folder).
- Deployment checklist: [DEPLOYMENT_TEST_LOG.md](DEPLOYMENT_TEST_LOG.md).
- App readiness before final docs: [APP_SUBMISSION_READINESS.md](APP_SUBMISSION_READINESS.md).
- Manual QA: [MANUAL_QA_CHECKLIST.md](MANUAL_QA_CHECKLIST.md).
- Architecture and **five-agent** workflow: [ARCHITECTURE.md](ARCHITECTURE.md) (includes Mermaid + [diagrams/architecture.mmd](diagrams/architecture.mmd)).
- Tool registry / contracts: [INTERFACE_CONTRACTS.md](INTERFACE_CONTRACTS.md), [`../tools/`](../tools/) modules.
- **TOOL3** written deliverable (export to **.docx** for Canvas, **after** URL + app freeze): [TOOL3_SUBMISSION_PACKAGE.md](TOOL3_SUBMISSION_PACKAGE.md) (aligns with [TOOL3.md](TOOL3.md) rubric).
