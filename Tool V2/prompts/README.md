# Agent prompts

System prompts are loaded by **`prompts/loader.py`** and combined with **`shared_guardrails.md`** for orchestrator roles `agent_2`–`agent_5`.

| File | Role |
|------|------|
| `agent_2_state_analyst.md` | Agent 2 — state data analyst (tools) |
| `agent_3_national_analyst.md` | Agent 3 — national data analyst (tools) |
| `agent_4_parent.md` | Agent 4 — state reporter (readable state summary) |
| `agent_5_national_reporter.md` | Agent 5 — national reporter (US-wide paragraph) |

Legacy / alternate copies may exist (`agent_2_state.md`, `agent_3_national.md`); the **loader** uses the `*_analyst` / `agent_4_parent` / `agent_5_national_reporter` filenames in `_ROLE_FILES`.
