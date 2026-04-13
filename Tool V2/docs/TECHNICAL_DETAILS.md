# Technical details

## API keys and environment variables

| Variable | Role |
|----------|------|
| **`SOCRATA_APP_TOKEN`** | Optional but recommended for CDC Socrata (higher rate limits, more reliable fetches). Child/teen tools require a token for direct Soda queries. |
| **`OPENAI_API_KEY`** | When set, orchestrator LLM steps prefer **OpenAI** Chat Completions; enables optional **function calling** for agents 2–3. |
| **`OPENAI_MODEL`** | Optional model name (default in code is typically `gpt-4o-mini` unless overridden). |
| **`OLLAMA_API_KEY`** | When OpenAI is not used, **Ollama Cloud** can serve LLM calls if this is set. |
| **`CONNECT_API_KEY`** (or publisher equivalents) | Used **locally** when publishing to Posit Connect with `deployment/deploy_me.py`, not by the Streamlit runtime unless your platform injects them. |

Secrets are often loaded from `.env` at the project root or `Tool V2/.env` (see `python-dotenv` usage in loaders and deploy script).

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

- Loaded from bundled CSV search paths (e.g. `Tool V2/data/measles_annual_1985.csv` and repo fallbacks); not a live API in the default path.

### LLM APIs

- **OpenAI:** HTTPS to OpenAI Chat Completions API (see `ollama_client.py` for paths and options).
- **Ollama Cloud:** HTTPS per Ollama client configuration when OpenAI is not used.

## Python packages (runtime)

Pinned in `Tool V2/requirements.txt` (minimum versions include):

- **streamlit** — UI
- **pandas**, **numpy** — data
- **requests** — HTTP to CDC / LLM
- **python-dotenv** — optional `.env` loading
- **plotly** — charts/maps
- **scikit-learn** — stage-1 model

Deployment may use `deployment/requirements-deploy.txt` for publisher-specific pins.

## File structure (main)

```
Tool V2/
  app.py                 # Streamlit entrypoint
  loaders.py             # CDC + CSV loaders
  ollama_client.py       # LLM client (OpenAI / Ollama)
  requirements.txt
  agents/                # Orchestrator
  contracts/             # Schemas
  prompts/               # Agent prompts (.md)
  risk/                  # Model and metrics
  tools/                 # Registry + CDC tool wrappers
  ui/                    # UI helpers (e.g. agent insights)
  tests/                 # Pytest
  deployment/            # deploy_me.py, smoke scripts
  docs/                  # Architecture, contracts, submission docs
```

## Deployment platform

- **Target:** **Posit Connect** (configurable server; default in `deployment/deploy_me.py` is `https://connect.systems-apps.com/`).
- **Publisher:** `rsconnect-python` via `python -m rsconnect.main deploy` (see `deployment/deploy_me.py`).
- **Environment forwarding:** Deploy script can pass `-E` for variables such as `SOCRATA_APP_TOKEN`, `OPENAI_API_KEY`, `OLLAMA_API_KEY`, `OPENAI_MODEL` so the hosted app can call CDC and LLMs.

Operational checklists: [`submission_notes.md`](submission_notes.md), [`DEPLOYMENT_TEST_LOG.md`](DEPLOYMENT_TEST_LOG.md).

## Related documents

- [`SYSTEM_ARCHITECTURE.md`](SYSTEM_ARCHITECTURE.md) — agents and data flow.
- [`USAGE_INSTRUCTIONS.md`](USAGE_INSTRUCTIONS.md) — how to use the live app.
