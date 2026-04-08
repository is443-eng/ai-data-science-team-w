# Tool V2 — Measles risk dashboard (App V2)

## Layout

| Path | Segment | Contents |
|------|---------|----------|
| `app.py` | UI | Streamlit entrypoint |
| `run_me.py` | — | Local dev launcher |
| `loaders.py`, `risk.py`, `ollama_client.py` | Core | Data, model, LLM client |
| `contracts/` | 0 | Shared `ToolOutput` / `AgentContext` dataclasses |
| `tools/` | 1 | CDC tool wrappers + `registry.py` |
| `agents/` | 2 | Orchestrator and multi-agent workflow |
| `prompts/` | 4 | Per-agent prompt templates (to be wired) |
| `utils/` | Core | Logging, state maps |
| `tests/` | 5 | Pytest suite |
| `baseline/` | 0 | Regression metrics JSON |
| `scripts/` | 0 | e.g. `capture_baseline.py` |
| `reference/shiny_v1_cdc/` | — | Legacy CDC API scripts (reference only) |
| `ui/` | 3 | Reusable Streamlit components (agent cards, loaders) |
| `deployment/` | 6 | `deploy_me.py` + Posit Connect notes (`rsconnect-python`) |
| `docs/` | 7 | Contracts, planning, submission notes |

## Run locally

```bash
python run_me.py
```

See `docs/planning/` for the full segmented build plan.
