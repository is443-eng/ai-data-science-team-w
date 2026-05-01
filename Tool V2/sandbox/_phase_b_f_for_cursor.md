## Phase B — Segment 3: Overview “Agent Insights” UI (detailed)

**Goal:** Surface the orchestrator’s four `AgentResult` payloads on the **Overview** tab under existing metrics, with **per-agent loading**, a **manual refresh** control, and **clear errors**—without changing the math or charts above the new section.

### B.1 Scope and placement

- **In scope:** New UI module(s) under [`ui/`](Tool%20V2/ui/), imports from [`app.py`](Tool%20V2/app.py) only for Overview (and shared sidebar if you add controls there).
- **Insertion point:** After the baseline **gauge** (Plotly) and **before** or **after** the “How is alarm… / How is baseline…” expanders—pick one and keep it consistent; recommended: **after the gauge row, before expanders**, so “Agent Insights” sits directly under the key visuals. Keep the **CSV download** block; place Agent Insights **above** or **below** it consistently (above download is fine).
- **Out of scope:** Rewriting non-Overview tabs in this segment unless the segmented plan’s “loading on all pages” is required—if so, treat as **B.5 optional**.

### B.2 Session state contract

Introduce dedicated keys (names are suggestions—use one consistent prefix, e.g. `agent_`):

| Key | Purpose |
|-----|---------|
| `agent_selected_state` | US state string for Agent 2 / context (default: e.g. “United States” or first alphabetically—match app conventions) |
| `agent_results` | `dict[AgentId, AgentResult]` or `None` until first run |
| `agent_context_snapshot` | Optional last `AgentContext` for debug expander |
| `agent_last_run_utc` | ISO timestamp for “Last refreshed” caption |
| `agent_run_id` | Correlates with orchestrator `request_id` |

Do **not** overload `ollama_summary` unless you intentionally merge legacy single-summary behavior; prefer separate keys to avoid regressions.

### B.3 Controls

- **State selector:** `st.selectbox` of state names (reuse the same list as **State risk** / forecast if available from `state_risk_df` or a static US-state list). Changing state should **not** auto-fire the pipeline until the user clicks refresh (predictable cost).
- **Primary button:** “Run / Refresh agent analysis” → builds `RiskFields` from `st.session_state` (`alarm_prob`, `baseline_tier`, `load_status`, `data_as_of`), calls `run_agent_pipeline(...)`, stores results.
- **Optional:** Checkbox “Include LLM agents (2–4)” to run Agent 1 only for faster CDC-only refresh—only if product-wise useful; otherwise omit to reduce branching.

### B.4 Loading and progressive rendering

| Approach | When to use |
|----------|-------------|
| **Single call, one spinner** | Fastest to implement; worse UX (all cards wait). |
| **Orchestrator callbacks or split functions** | Expose `run_agent1_only`, then `run_llm_agents(context)` so the UI can update after Agent 1. |
| **`st.status` or four `st.empty` placeholders** | Update each placeholder when that agent completes (requires refactor from one blocking `run_agent_pipeline` or internal yielding—may be Phase B stretch). |

**Minimum acceptable:** Spinner around the whole Agent Insights block until the pipeline returns; **stretch goal:** show Agent 1 summary first, then 2–4 as they complete (depends on orchestrator refactor from Phase A).

### B.5 Optional: loading hints on other tabs

Segmented plan mentions loading indicators on **other** pages. Practical approach: ensure **sidebar** shows global `data_as_of` and `load_status` (already partially present); add a thin `st.caption("Loading…")` only where long recomputes exist. Do not block Segment 3 on this—document as follow-up if timeboxed.

### B.6 Card layout

Four `st.subheader` + `st.container` blocks (or expanders) for **Agent 1 – Data package**, **Agent 2 – State focus**, **Agent 3 – National**, **Agent 4 – Parent brief**. Map `AgentResult.status`: `success` → render `content`; `error` → `st.error(error_message)`; include `warnings` as `st.warning` bullets.

### B.7 Regression checklist (must pass before merge)

- Overview metrics, gauge, expanders, and download behave as before.
- Other five tabs render without import errors; spot-check one chart per tab.
- With `OLLAMA_API_KEY` unset: agent cards show readable errors, app does not crash.

### B.8 Definition of done (Phase B)

- [`ui/agent_insights.py`](Tool%20V2/ui/) (or equivalent) implements the section; [`app.py`](Tool%20V2/app.py) Overview calls it with session state.
- User can select state, refresh, and see four cards with last-run timestamp.
- Manual smoke documented (screenshot or short checklist in PR).

---

## Phase C — Segment 4: Model and prompts (detailed)

**Goal:** Align cloud model choice with the segmented plan (**`gemma4:31b-cloud` preferred**), externalize **per-agent** system prompts, and enforce **guardrails** so outputs stay trustworthy in the UI.

### C.1 Model stack

- Update [`ollama_client.py`](Tool%20V2/ollama_client.py) `OLLAMA_MODELS` tuple: put **`gemma4:31b-cloud`** first, then existing fallbacks (`gpt-oss:20b-cloud`, etc.) for resilience.
- **Single source of truth:** All chat paths (legacy `get_ollama_*` helpers **and** orchestrator LLM calls) should iterate the same tuple or call a shared `chat_completion` helper (ties to Phase A.5).
- **Timeouts:** Keep 90s default unless Connect or Ollama docs suggest otherwise; log model used on success.

### C.2 Prompt file layout ([`prompts/`](Tool%20V2/prompts/))

| File | Audience |
|------|----------|
| `agent_2_state.md` | System (or system+instructions) for state-focused agent |
| `agent_3_national.md` | National summary agent |
| `agent_4_parent.md` | Concerned-parent voice; references Agent 2 output |
| `shared_guardrails.md` | Injected into all agents: no fabricated numbers, cite `data_as_of`, short sections |

Optional: `agent_1_data.md` only if Agent 1 produces natural language (today it is tool aggregation—likely **no** LLM for Agent 1).

### C.3 Prompt loader

- Add [`prompts/loader.py`](Tool%20V2/prompts/) (or `utils/prompt_loader.py`): `load_prompt(name: str) -> str` reading adjacent `.md` files, with cache for Streamlit reruns.
- **Fail safe:** If a file is missing, log error and use a one-line inline fallback so the app still runs in dev.

### C.4 Refactor existing Ollama helpers

- Gradually migrate [`get_ollama_summary`](Tool%20V2/ollama_client.py), forecast/WW/state helpers to use **`chat_completion(system, user)`** with guardrails prepended from `shared_guardrails.md`.
- Preserve behavior for dashboard sections that are not yet on the orchestrator path until Segment 3/5 QA confirms parity.

### C.5 Orchestrator alignment

- Orchestrator Agents 2–4 load **role** prompts from `agent_2_state.md` etc.; **user** payload remains structured context from `AgentContext` (serialized JSON or bullet list—keep under token limits per existing `MAX_PROMPT_CHARS` pattern).

### C.6 Guardrails checklist (review before ship)

- [ ] Prompts state: “Use only numbers and dates present in the context.”
- [ ] Prompts require mentioning **data as of** when citing trends.
- [ ] Agent 4 instructed not to give medical directives; “see CDC” link allowed (match existing forecast helper style).
- [ ] Spot-check 3 runs: no numeric hallucination vs input context.

### C.7 Definition of done (Phase C)

- `OLLAMA_MODELS` reflects `gemma4:31b-cloud` first; prompts live under [`prompts/`](Tool%20V2/prompts/) and are loaded by code.
- At least one manual run confirms model tag in logs or response path.
- Documentation updated (one paragraph in technical doc) listing model order and prompt files.

---

## Phase D — Segment 5: Quality gate (detailed)

**Goal:** Prove **backward compatibility**, **orchestrator correctness**, and **deploy readiness** before treating the app as release-quality.

### D.1 Automated tests

| Suite | Command / scope |
|-------|-----------------|
| Full Tool V2 | `cd "Tool V2" && python3 -m pytest tests/ -v` (adjust `python` as needed) |
| New | [`tests/test_orchestrator.py`](Tool%20V2/tests/) from Phase A |
| Existing | Registry, tool schema, live parity tests—decide if **live** tests require `SOCRATA_APP_TOKEN` and mark `@pytest.mark.integration` if you split them |

**CI recommendation:** Default job runs **mocked** tests only; optional nightly job with secrets for live CDC.

### D.2 Manual regression matrix (record pass/fail)

| Area | Check |
|------|--------|
| Overview | Metrics, gauge, expanders, CSV download, **Agent Insights** refresh |
| Historical | Line chart, NNDSS weekly controls |
| Kindergarten | Map/table, year selector |
| Wastewater vs NNDSS | Dual chart, audit expander |
| State risk | Choropleth/table tiers |
| Forecast | Table, AI expander if enabled |
| Sidebar | Refresh data, debug panel if enabled |

### D.3 Baseline comparison

- Reference [`baseline/baseline_metrics.json`](Tool%20V2/baseline/baseline_metrics.json): **row counts** and `load_status` may drift as CDC updates; compare **structure** (keys present) and order-of-magnitude, not exact counts, unless you re-run [`scripts/capture_baseline.py`](Tool%20V2/scripts/capture_baseline.py) after a deliberate refresh.
- Document in PR: “baseline recaptured” or “expected CDC drift.”

### D.4 Edge-case pass

- Missing `.env` token: app warns, no stack trace.
- Partial CDC failure: Overview and tools show degraded state per contracts.
- Missing Ollama key: LLM sections fail gracefully.

### D.5 Definition of done (Phase D)

- `pytest` green for required markers.
- Manual matrix signed off (name + date).
- No open **blocker** defects for TOOL2 features (orchestration + tools + deploy path).

---

## Phase E — Segment 6: Deploy and record URL (detailed)

**Goal:** Production app on **Posit Connect** with documented env vars and a **stable URL** for Canvas submission.

### E.1 Preconditions

- [`deployment/requirements-deploy.txt`](Tool%20V2/deployment/requirements-deploy.txt) installed in the venv you deploy from.
- API key for Connect set (`CONNECT_API_KEY` or aliases per [`deployment/README.md`](Tool%20V2/deployment/README.md)).
- Repo root `.env` has `SOCRATA_APP_TOKEN` (and `OLLAMA_API_KEY` if AI should work live).

### E.2 Dry run

```bash
cd "Tool V2"
python3 deployment/deploy_me.py --dry-run
```

Verify printed `rsconnect` argv: correct `app.py`, Python version, excludes (`tests`, `docs`, etc.).

### E.3 First deploy vs update

- **First deploy:** `python3 deployment/deploy_me.py` — note the new content URL / GUID from Connect UI.
- **Updates:** reuse `--app-id <guid>` to avoid duplicate listings (see deployment README).

### E.4 Runtime env on Connect

- Confirm **`SOCRATA_APP_TOKEN`** and **`OLLAMA_API_KEY`** appear under Connect → content → **Vars** (either forwarded by `-E` at deploy time or set manually).
- Redeploy or restart content after changing vars if required by your server policy.

### E.5 Smoke test (deployed)

| Step | Pass criteria |
|------|----------------|
| Open URL (incognito) | App loads, no 500 |
| Overview | Metrics visible (token present) |
| One other tab | e.g. Historical chart renders |
| Agent section | Errors OK if key missing; success if key present |

### E.6 Record and rollback

- Paste **HTTPS app URL** into [`docs/submission_notes.md`](Tool%20V2/docs/submission_notes.md) and README if desired.
- **Rollback:** Redeploy previous git tag with `--app-id` to same content, or restore vars from backup.

### E.7 Definition of done (Phase E)

- Working public (or course-appropriate) URL documented.
- At least one teammate verified from a non-dev machine or incognito.

---

## Phase F — Segment 7: Submission package (detailed)

**Goal:** Meet [`TOOL2.md`](Tool%20V2/docs/planning/TOOL2.md): **single docx** with GitHub link, **deployed app link**, and pointers to documentation that answer each rubric item.

### F.1 Rubric mapping (use as doc outline)

| Points | Rubric item | What to include |
|--------|-------------|-------------------|
| 25 | Agentic orchestration | Diagram + prose: Agent 1–4 roles, order, parallel 2∥3 |
| 25 | Tool calling (or RAG) | Table: each `tool_name`, CDC source, parameters, return shape |
| 10 | UI / visual design | Screenshots: Overview with Agent Insights, one other tab |
| 10 | Deployed link | Paste URL; confirm password if any |
| 10 | Description (3–5 ¶) | Stakeholders, APIs, new features, value |
| 10 | Process diagram | Data flow including tools + agents (export from Mermaid or draw.io) |
| 10 | Technical documentation | Architecture, tools, keys, packages, file tree, deployment |
| 0 | Team roles | Table: name → role |

### F.2 Repo documentation artifacts

| Artifact | Suggested location |
|----------|-------------------|
| Architecture | [`docs/ARCHITECTURE.md`](Tool%20V2/docs/ARCHITECTURE.md) (create) or extend [`INTERFACE_CONTRACTS.md`](Tool%20V2/docs/INTERFACE_CONTRACTS.md) |
| Tools reference | `docs/TOOLS.md` listing registry |
| User / instructor guide | `docs/DOCUMENTATION.md` or top-level [`README.md`](Tool%20V2/README.md) pointer |
| Process diagram source | [`docs/app-flow-executive.mmd`](docs/app-flow-executive.mmd) **or** `Tool V2/docs/app_v2_flow.mmd` |

### F.3 Single docx structure (recommended)

1. Title + team + course
2. **GitHub** repo URL (main branch landing)
3. **Live app** URL (Connect)
4. **Description** (3–5 paragraphs)
5. **Process diagram** (image embed)
6. **Technical** section (architecture, tools, env vars, deployment platform)
7. **How to use** deployed app (steps, credentials if any)
8. **Where to find** detailed docs in repo (bullet list with paths)
9. **Team roles**

### F.4 Accuracy review

- [ ] Diagram matches **current** code (orchestrator + registry), not an old draft.
- [ ] Model name (`gemma4:31b-cloud`) matches `ollama_client`.
- [ ] Tool table matches [`INTERFACE_CONTRACTS.md`](Tool%20V2/docs/INTERFACE_CONTRACTS.md).

### F.5 Definition of done (Phase F)

- [`docs/submission_notes.md`](Tool%20V2/docs/submission_notes.md) filled with repo URL + app URL + doc pointers.
- Docx exported; one teammate read-through for typos and broken links.
- Canvas submission checklist satisfied.

---

