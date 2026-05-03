# App V3 interface contracts (Tool V3)

Frozen JSON-oriented shapes for the tool layer, orchestrator, and UI. Field names are **snake_case**. All timestamps are ISO-8601 strings where applicable.

## Ownership (handoff)

| Area | Owner role | Delivers to |
|------|------------|-------------|
| Tool wrappers + registry | Backend / Data | Orchestration: `ToolOutput` per tool name |
| Orchestrator + agents | Agent engineer | UI: `AgentResult` per `agent_id` |
| Streamlit Overview | Frontend | QA: screenshots + loading behavior checklist |

## Error format (orchestration and tools)

API failures should surface as `ToolOutput.status == "error"` (or `"partial"` when some rows returned) with `errors: string[]` and optional structured detail:

```json
{
  "code": "HTTP_TIMEOUT",
  "message": "CDC Socrata request exceeded 90s",
  "retryable": true,
  "detail": { "view_id": "x9gk-5huc" }
}
```

Use `contracts.schemas.ToolErrorDetail` for the same shape when attaching to metadata.

## `ToolInput`

```json
{
  "tool_name": "nndss",
  "parameters": {}
}
```

Parameters remain backward-compatible with V1 dashboard semantics (Segment 1 fills these per tool).

## Registered tool names (Segment 1)

| `tool_name` | Module | Source / notes |
|-------------|--------|----------------|
| `child_vax` | `tools/child_vax_tool.py` | CDC `fhky-rtsk` (0–35 mo MMR); default WHERE matches V1 script |
| `kindergarten_vax` | `tools/kindergarten_vax_tool.py` | Same as `loaders.load_kindergarten` (`ijqb-a7ye`) |
| `teen_vax` | `tools/teen_vax_tool.py` | CDC `ee48-w5t6` (13–17 MMR); default WHERE matches V1 script |
| `wastewater` | `tools/wastewater_tool.py` | Same as `loaders.load_wastewater` (`akvg-8vrb`) |
| `nndss` | `tools/nndss_tool.py` | Same as `loaders.load_nndss` (`x9gk-5huc`) |

Dynamic dispatch: `tools.registry.run_tool(name, parameters)`. Unknown `name` returns `ToolOutput` with `status: "error"` and `errors` containing `unknown_tool:…` plus `known_tools:…`.

Shared parameters (where supported): `use_cache` (bool, default `true`) for loader-backed tools; `limit`, `timeout_s`, optional `where` for child/teen (see tool modules).

## `ToolOutput`

```json
{
  "tool_name": "nndss",
  "status": "success",
  "source": "cdc_socrata",
  "as_of": "2026-04-07 12:00",
  "data": {},
  "errors": [],
  "metadata": {}
}
```

## `AgentContext` (after Agent 1)

```json
{
  "request_id": "uuid-or-streamlit-run-id",
  "selected_state": "California",
  "data_as_of": "2026-04-07 12:00",
  "tool_outputs": {},
  "alarm_probability": 0.42,
  "baseline_tier": "medium",
  "load_status": { "historical": "ok", "kindergarten": "ok" },
  "extra": {
    "baseline_explanation": "…",
    "baseline_score": 72.5,
    "state_risk_snapshot": "…",
    "state_risk_records_json": "[{\"state\":\"…\",\"total_risk\":…}]",
    "national_weekly_trend_json": "[{\"year\":2026,\"week\":12,\"cases\":…}]"
  }
}
```

`tool_outputs` maps tool name → `ToolOutput` object.

`extra` (optional keys used by orchestrator LLM steps):

| Key | Purpose |
|-----|---------|
| `baseline_explanation` | Text from `get_baseline_risk_components` for LLM attribution |
| `baseline_score` | Overview baseline gauge 0–100 (may be harmonized with state composite max) |
| `state_risk_snapshot` | One-state composite lines when a state is selected |
| `state_risk_records_json` | JSON array of state risk rows for leaderboard / tier tools |
| `national_weekly_trend_json` | Serialized national weekly series for national activity trend tool |

## `AgentResult` (per card on Overview)

```json
{
  "agent_id": "agent_5",
  "status": "success",
  "content": "…",
  "error_message": null,
  "started_at": "2026-04-07T12:00:01Z",
  "completed_at": "2026-04-07T12:00:08Z",
  "warnings": []
}
```

`status` is one of: `pending`, `running`, `success`, `error`.

## `InsightQCResult` (optional — insight quality rubric)

Returned when **`INSIGHT_QC_ENABLED=1`** scores national or state reporter output. Dataclass: `contracts.schemas.InsightQCResult`.

```json
{
  "role": "national",
  "status": "success",
  "passed": true,
  "overall_score": 4.2,
  "accurate": true,
  "scores": {},
  "details": "…",
  "error_message": null
}
```

- **`role`:** `"national"` | `"state"`.
- **`status`:** e.g. `success`, `skipped`, `error` (see `InsightQCStatus` in code).

## `OrchestratorRun` (orchestrator return value)

The pipeline returns a bundle used by the UI (not all fields are persisted to JSON on disk):

| Field | Type | Purpose |
|-------|------|---------|
| `context` | `AgentContext` | Request id, tool outputs, metrics, `extra` blocks for LLMs |
| `results` | `dict[str, AgentResult]` | Keys such as `agent_1` … `agent_5` |
| `insight_quality` | `dict[str, InsightQCResult]` | Optional QC entries (e.g. national/state keys used by the Overview expander) |

`OrchestratorRun.to_json_dict()` includes `insight_quality` for debugging and tests (`agents/orchestrator.py`).

## Latency expectations (planning, not SLAs)

| Step | Typical |
|------|---------|
| Single tool call (cached) | &lt; 1 s |
| Single tool call (live CDC) | 5–90 s |
| Agent 1 (all tools) | dominated by slowest tool |
| Agents 2 + 3 in parallel | LLM latency × 1 |
| Agents 4 + 5 in parallel (after 2/3) | LLM latency × 1 |

## Code reference

Python dataclasses live in `contracts/schemas.py` with `to_json_dict()` helpers.

## Sign-off checklist

- [ ] Tool owner: `ToolInput` / `ToolOutput` field names stable for registry consumers.
- [ ] Orchestration owner: `AgentContext`, `AgentResult`, optional **`InsightQCResult`** / **`OrchestratorRun.insight_quality`** documented for UI and tests.
- [ ] UI owner: `AgentResult.content` display rules (string vs structured) and QC expander behavior when enabled.
