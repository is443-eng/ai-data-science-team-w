# Tool V3 — Measles risk dashboard (App V3)

Streamlit app: CDC data loaders, risk models (alarm, forecast, **state composite** scores), multi-tab charts, and **agentic Insights** (five LLM agents after a unified tool run).

## Layout

| Path | Contents |
|------|----------|
| `app.py` | Streamlit entrypoint |
| `run_me.py` | Local dev launcher |
| `loaders.py`, `risk.py`, `ollama_client.py` | Data, models, LLM client |
| `contracts/` | `ToolOutput` / `AgentContext` / `AgentResult` |
| `tools/` | CDC tool wrappers + `registry.py` |
| `agents/` | Orchestrator (**Agents 1–5**) |
| `prompts/` | Per-agent system prompts (`loader.py` + `shared_guardrails.md`) |
| `ui/` | `agent_insights.py` (Overview Insights block) |
| `utils/` | Logging, state maps |
| `tests/` | Pytest (orchestrator, risk, tools, national trend) |
| `deployment/` | `deploy_me.py`, Posit Connect notes |
| `docs/` | **Architecture, interface contracts, submission package, QA checklists** |

## Run locally

```bash
cd "Tool V3"
python run_me.py
```

Set `SOCRATA_APP_TOKEN` in a `.env` at repo root or in `Tool V3/` for reliable CDC pulls. For **Insights**, set `OPENAI_API_KEY` and/or `OLLAMA_API_KEY`.

## Deployed app (Posit Connect)

- **Direct:** https://connect.systems-apps.com/content/b8cfc1fa-8eb0-4c2e-ba98-b5f06837e933/
- **Demo video (YouTube):** https://youtu.be/bpEJRjsjYyc

See **[`docs/submission_notes.md`](docs/submission_notes.md)** for dashboard link, deploy commands, and env forwarding.

## Documentation

Start at **[`docs/README.md`](docs/README.md)** (TOOL3 submission package index, architecture, contracts). Course rubric: **[`docs/TOOL3.md`](docs/TOOL3.md)**.
