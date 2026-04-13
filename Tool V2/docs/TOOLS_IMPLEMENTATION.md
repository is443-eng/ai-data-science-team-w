# Tool implementation (CDC data sources)

This submission uses **retrieval via CDC Socrata APIs and local loaders**, wrapped as **named tools** with a stable registry. It does **not** use a separate **vector database** or **embedding-based RAG**; the “retrieval” is **structured public-health data fetch** (and optional caching), then **JSON-oriented `ToolOutput`** payloads for the orchestrator.

## Registry

- **Module:** `tools/registry.py`
- **Dispatch:** `run_tool(tool_name, parameters)` → `ToolOutput`
- **Registered names:** `child_vax`, `kindergarten_vax`, `teen_vax`, `wastewater`, `nndss`
- **Unknown name:** Returns `ToolOutput` with `status: "error"` and `errors` listing known tools.

## Common return shape: `ToolOutput`

Each tool returns a `ToolOutput` (see `contracts/schemas.py` and [`INTERFACE_CONTRACTS.md`](INTERFACE_CONTRACTS.md)) with fields including:

| Field | Meaning |
|-------|---------|
| `tool_name` | Registry name |
| `status` | `success`, `partial`, or `error` |
| `source` | e.g. `cdc_socrata:<view_id>` |
| `as_of` | UTC timestamp string |
| `data` | JSON-serializable payload (often tabular rows) |
| `errors` | List of machine-readable error strings |
| `metadata` | View ID, parameters echoed, loader status, etc. |

Loader-backed tools serialize DataFrames via helpers in `tools/_common.py` (e.g. `dataframe_to_json_payload`).

## Tools (name, purpose, parameters, returns)

### `child_vax`

| | |
|--|--|
| **Purpose** | CDC **0–35 month** MMR coverage (`fhky-rtsk`), V1-compatible defaults. |
| **Parameters** | `limit` (default 50_000), `timeout_s` (default 90), `where` (optional; default matches V1 `CHILD_DEFAULT_WHERE`), `retries` (default 3). Requires **`SOCRATA_APP_TOKEN`**. |
| **Returns** | `ToolOutput` with cleaned coverage rows in `data`, or `status: "error"` if token missing or HTTP fails. |

### `kindergarten_vax`

| | |
|--|--|
| **Purpose** | Kindergarten MMR coverage — wraps `loaders.load_kindergarten` (CDC `ijqb-a7ye`). |
| **Parameters** | `use_cache` (bool, default `true`). |
| **Returns** | `ToolOutput` with tabular JSON in `data`; errors if load fails. |

### `teen_vax`

| | |
|--|--|
| **Purpose** | CDC **13–17** MMR coverage (`ee48-w5t6`), V1-compatible defaults. |
| **Parameters** | Same pattern as `child_vax`: `limit`, `timeout_s`, `where` (default `TEEN_DEFAULT_WHERE`), `retries`. Requires **`SOCRATA_APP_TOKEN`**. |
| **Returns** | `ToolOutput` with teen coverage rows or error payload. |

### `wastewater`

| | |
|--|--|
| **Purpose** | Wastewater measles signal — wraps `loaders.load_wastewater` (CDC `akvg-8vrb`). |
| **Parameters** | `use_cache` (bool, default `true`). |
| **Returns** | `ToolOutput` with wastewater rows in `data`; errors on fetch failure. |

### `nndss`

| | |
|--|--|
| **Purpose** | NNDSS measles line list — wraps `loaders.load_nndss` (CDC `x9gk-5huc`). |
| **Parameters** | `use_cache` (bool, default `true`). |
| **Returns** | `ToolOutput` with NNDSS rows in `data`; errors on load failure. |

## Agent 1 usage

The orchestrator runs **all five tools** in a **fixed order** so downstream agents always see a full tool trace for the run (subject to individual tool errors).

## Optional OpenAI tools (agents 2–3)

When using OpenAI with function calling, additional **handler-backed tools** can answer leaderboard / trend questions from `ctx.extra` (e.g. `state_risk_records_json`, `national_weekly_trend_json`). Those are orchestration helpers, not separate CDC registry tools.

## Related documents

- [`INTERFACE_CONTRACTS.md`](INTERFACE_CONTRACTS.md) — full contract details and JSON examples.
- [`SYSTEM_ARCHITECTURE.md`](SYSTEM_ARCHITECTURE.md) — how tools fit into the five-agent pipeline.
