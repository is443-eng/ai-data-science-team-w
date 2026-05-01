# System architecture (Tool V2)

This document describes **agent roles**, **end-to-end workflow**, and **how major components interact** in the Predictive Measles Risk Dashboard with agentic orchestration.

## System purpose

The Streamlit application loads **public CDC surveillance and coverage data**, runs a **risk model** (alarm probability, state composite scores, baseline gauge, forecast inputs), and renders interactive charts and maps. **Tool V2** adds an **orchestrator** that runs CDC-backed **tools** first, then **LLM agents** that produce state-level and national narratives grounded in tool output and dashboard metrics.

## Component overview

| Layer | Location (conceptual) | Responsibility |
|-------|----------------------|----------------|
| Data | `loaders.py` | Fetch or load kindergarten coverage, wastewater, NNDSS, and historical CSV; report per-source status. |
| Risk model | `risk/` | Stage-1 alarm fit/predict, national weekly NNDSS aggregation, per-state composite (`get_state_risk_df`), baseline gauge (`get_baseline_risk`), forecast helpers. |
| UI | `app.py`, `ui/` | Tabs: Overview, Historical, Kindergarten, Wastewater vs NNDSS, State risk, Forecast; Overview integrates orchestrator insights. |
| Tools | `tools/*.py`, `tools/registry.py` | Five named tools wrapping CDC Socrata (and loaders); return structured `ToolOutput`. |
| Orchestration | `agents/orchestrator.py` | Runs Agent 1 then parallel LLM steps; prompts from `prompts/*.md`. |
| LLM client | `ollama_client.py` | OpenAI Chat Completions when configured, else Ollama Cloud. |
| Contracts | `contracts/schemas.py` | `ToolOutput`, `AgentContext`, `AgentResult` for consistent payloads. |

## Workflow (data to UI)

1. **Load:** `load_all` pulls loader-backed datasets and merges load status; the app caches and displays “data as of” messaging.
2. **Model:** Risk functions compute alarm probability, state risk table, baseline tier/score (with optional harmonization against state composites), and forecast-related outputs used on Forecast and Overview.
3. **UI:** Each tab consumes session state populated after load; Overview shows the baseline gauge and optional **Generate insights** block fed by the orchestrator.
4. **Orchestrator (on demand):** **Agent 1** runs all five registry tools in a fixed order. **Agents 2 and 3** run **in parallel** (state vs national analyst LLM). **Agents 4 and 5** run **in parallel** (state vs national reporter LLM). Reporters feed text back to the Overview insights area.

**Order:** Agent 1 → (Agent 2 ∥ Agent 3) → (Agent 4 ∥ Agent 5). If Agent 2 fails, Agent 4 is skipped.

## Agent roles

| Agent | Role | Primary inputs | Output use |
|-------|------|----------------|------------|
| **1** | Deterministic tool runner | Registry + per-tool parameters | `ToolOutput` map in `AgentContext` |
| **2** | State data analyst (LLM) | Metrics, state-filtered excerpts, `ctx.extra` (e.g. state risk JSON) | Raw analyst text → Agent 4 |
| **3** | National data analyst (LLM) | Metrics, tool summaries, national trend JSON | Raw analyst text → Agent 5 |
| **4** | State reporter (LLM) | Agent 2 output + context | Overview **state** summary (when a state is selected) |
| **5** | National reporter (LLM) | Agent 3 output + ranking / tier blocks | Overview **national** summary |

Agents 2–3 may use **OpenAI tool/function calling** when an API key and structured context are available; otherwise context is injected as plain text (e.g. Ollama path).

## How components interact

- **Loaders → Risk:** DataFrames drive model fits and composite scores.
- **Loaders / session → Orchestrator:** Agent 1 re-fetches via tools so insights align with the same CDC pulls where possible; `ctx.extra` carries baseline explanation, state risk JSON, national weekly JSON, etc.
- **Orchestrator → UI:** `AgentResult.content` strings render on Overview under insights.
- **Prompts:** `prompts/loader.py` loads markdown prompts; combined prompts are size-bounded so national summaries keep ranking blocks before long dumps.

## Process diagram

The same architecture diagram is maintained as editable Mermaid in [`diagrams/architecture.mmd`](diagrams/architecture.mmd) (export to PNG/SVG for reports per [`diagrams/README.md`](diagrams/README.md)) and embedded in [`ARCHITECTURE.md`](ARCHITECTURE.md).

## Related documents

- [`TOOLS_IMPLEMENTATION.md`](TOOLS_IMPLEMENTATION.md) — tool names, parameters, and return shapes.
- [`TECHNICAL_DETAILS.md`](TECHNICAL_DETAILS.md) — environment variables, endpoints, packages, deployment.
- [`USAGE_INSTRUCTIONS.md`](USAGE_INSTRUCTIONS.md) — using the deployed app.
