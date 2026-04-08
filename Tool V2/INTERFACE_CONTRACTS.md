# App V2 interface contracts (Segment 0)

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
  "baseline_tier": "elevated",
  "load_status": { "historical": "ok", "kindergarten": "ok" },
  "extra": {}
}
```

`tool_outputs` maps tool name → `ToolOutput` object.

## `AgentResult` (per card on Overview)

```json
{
  "agent_id": "agent_2",
  "status": "success",
  "content": "…",
  "error_message": null,
  "started_at": "2026-04-07T12:00:01Z",
  "completed_at": "2026-04-07T12:00:08Z",
  "warnings": []
}
```

`status` is one of: `pending`, `running`, `success`, `error`.

## Latency expectations (planning, not SLAs)

| Step | Typical |
|------|---------|
| Single tool call (cached) | &lt; 1 s |
| Single tool call (live CDC) | 5–90 s |
| Agent 1 (all tools) | dominated by slowest tool |
| Agent 2 + 3 in parallel | LLM latency × 1 |
| Agent 4 (after Agent 2) | LLM latency |

## Code reference

Python dataclasses live in `contracts/schemas.py` with `to_json_dict()` helpers.

## Sign-off checklist (Segment 0)

- [ ] Tool owner: `ToolInput` / `ToolOutput` field names approved for Segment 1.
- [ ] Orchestration owner: `AgentContext` and `AgentResult` approved for Segment 2–3.
- [ ] UI owner: `AgentResult.content` display rules (string vs structured) noted for Segment 3.
