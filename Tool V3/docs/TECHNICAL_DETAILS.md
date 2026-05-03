# Technical details (Tool V3)

## API keys and environment variables

| Variable | Role |
|----------|------|
| **`SOCRATA_APP_TOKEN`** | Optional but recommended for CDC Socrata (higher rate limits, more reliable fetches). Child/teen tools require a token for direct Soda queries. |
| **`OPENAI_API_KEY`** | When set, orchestrator LLM steps prefer **OpenAI** Chat Completions; enables optional **function calling** for agents 2–3. |
| **`OPENAI_MODEL`** | Optional model name (default in code is typically `gpt-4o-mini` unless overridden). |
| **`OLLAMA_API_KEY`** | When OpenAI is not used, **Ollama Cloud** can serve LLM calls if this is set. |
| **`INSIGHT_QC_ENABLED`** | Set to `1` to run optional rubric scoring on national/state insight text (`INSIGHT_QC_MIN_OVERALL`, `INSIGHT_QC_REQUIRE_ACCURATE`). |
| **`INSIGHT_REFINEMENT_ENABLED`** | Set to `1` with QC enabled for optional refinement rounds (`INSIGHT_REFINEMENT_MIN_ROUNDS`, `INSIGHT_REFINEMENT_MAX_ROUNDS`). |
| **`CONNECT_API_KEY`** (or publisher equivalents) | Used **locally** when publishing to Posit Connect with `deployment/deploy_me.py`, not by the Streamlit runtime unless your platform injects them. |

Secrets are loaded from `.env` at the **project root** or **`Tool V3/.env`** (see `python-dotenv` in loaders, client, and deploy script).

## Endpoints and data sources

### CDC Socrata (Soda API)

- **Query base (v3):** `https://data.cdc.gov/api/v3/views/<VIEW_ID>/query.json`  
  Requests use `POST` with JSON body (`query`, `page`); headers include `X-App-Token` when a token is set.

### Dataset view IDs (used in loaders / tools)

| View ID | Dataset (summary) |
|---------|-------------------|
| `ijqb-a7ye` | Kindergarten MMR coverage |
| `akvg-8vrb` | Wastewater measles surveillance |
| `x9gk-5huc` | NNDSS measles |
| `fhky-rtsk` | Child (0–35 mo) MMR coverage |
| `ee48-w5t6` | Teen (13–17) MMR coverage |

### Historical national cases

- Loaded from bundled CSV search paths (e.g. `Tool V3/data/measles_annual_1985.csv` and repo fallbacks); not a live API in the default path.

### LLM APIs

- **OpenAI:** HTTPS to OpenAI Chat Completions API (see `ollama_client.py`).
- **Ollama Cloud:** HTTPS per `ollama_client.py` when OpenAI is not used.

## Python packages (runtime)

Declared in **`Tool V3/requirements.txt`** (minimum versions include):

- **streamlit** — UI  
- **tornado** — required on **Posit Connect** for the bundled Streamlit runtime (`connect_streamlit_runtime.py`)  
- **pandas**, **numpy** — data  
- **requests** — HTTP to CDC / LLM  
- **python-dotenv** — optional `.env` loading  
- **plotly** — charts/maps  
- **scikit-learn**, **scipy** — stage-1 model and stats (`risk.py` imports **scipy** directly)  
- **pytest** — tests (included in bundle today; optional split to dev-only for smaller images)

Deployment publisher deps: `deployment/requirements-deploy.txt` (`rsconnect-python`).

## File structure (main)

```
Tool V3/
  app.py                 # Streamlit entrypoint
  loaders.py             # CDC + CSV loaders
  ollama_client.py       # LLM client (OpenAI / Ollama)
  requirements.txt
  .python-version        # 3.12.4 (Posit Connect local env match)
  agents/                # Orchestrator, insight QC, regression helpers
  contracts/             # Schemas (ToolOutput, AgentContext, AgentResult, InsightQCResult)
  prompts/               # Agent prompts (.md)
  risk.py                # Model and metrics
  tools/                 # Registry + CDC tool wrappers
  ui/                    # UI helpers (e.g. agent insights)
  tests/                 # Pytest
  deployment/            # deploy_me.py, smoke scripts
  docs/                  # Architecture, contracts, TOOL3 submission package
```

## Deployment platform (as deployed)

- **Server:** **Posit Connect** — `https://connect.systems-apps.com/`
- **Live content (direct):** https://connect.systems-apps.com/content/b8cfc1fa-8eb0-4c2e-ba98-b5f06837e933/
- **Publisher:** `rsconnect-python` via `python -m rsconnect.main deploy` (see `deployment/deploy_me.py`).
- **Python:** **3.12.4** on Connect (`--override-python-version` / `.python-version`).
- **Environment forwarding:** Deploy script passes `-E` for `SOCRATA_APP_TOKEN`, `OPENAI_API_KEY`, `OLLAMA_API_KEY`, `OPENAI_MODEL` when set locally so the hosted app can call CDC and LLMs.

Operational checklists: [`submission_notes.md`](submission_notes.md), [`DEPLOYMENT_TEST_LOG.md`](DEPLOYMENT_TEST_LOG.md).

## Related documents

- [`SYSTEM_ARCHITECTURE.md`](SYSTEM_ARCHITECTURE.md) — agents and data flow.
- [`USAGE_INSTRUCTIONS.md`](USAGE_INSTRUCTIONS.md) — how to use the live app.
- [`INTERFACE_CONTRACTS.md`](INTERFACE_CONTRACTS.md) — JSON shapes including QC.
- [`TOOL3.md`](TOOL3.md) — course rubric.
