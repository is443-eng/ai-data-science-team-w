# Usage instructions (deployed app)

## Live application URL

Paste your team’s **Posit Connect** app URL here after deployment (same slot as in [`submission_notes.md`](submission_notes.md)):

- **Live app URL:** https://019d8308-dd30-7f63-8ef8-b1aee7428736.share.connect.posit.cloud/

The app title in the browser should be **Risk of Measles Outbreak in US**.

## What the app does (quick orientation)

- **Sidebar:** Choose a **page** (tab), optionally **Refresh data** to bypass cache and reload CDC data.
- **Overview:** Baseline risk tier and **baseline risk meter** (0–100); optional **Generate insights** for AI-generated state/national summaries when LLM keys are configured on the server.
- **Historical trends:** National historical cases, NNDSS weekly series, model interpretation expanders, CSV download of summary metrics.
- **Kindergarten coverage:** State map and table by selected school year (when years are available in the data).
- **Wastewater vs NNDSS:** Detection frequency vs reported cases; optional **Generate AI report** on that tab (Ollama path when configured).
- **State risk:** Map and table of composite scores; optional per-state AI report.
- **Forecast:** Outlook-style table and optional **Generate AI interpretation**.

## Typical session

1. Open the live URL and wait for the first load (CDC fetches can take time).
2. Check **sidebar** captions for data source status and **Data as of** timestamp.
3. Start from **Overview** for the headline gauge; use other tabs for detail.
4. Use **Refresh data** if you need a fresh pull after upstream CDC updates (subject to cache and rate limits).

## If something fails

- **Empty or error states:** Note sidebar source lines (e.g. kindergarten or NNDSS unavailable). The app is designed to degrade gracefully with warnings.
- **No AI text:** Hosted environment may be missing **`OPENAI_API_KEY`** or **`OLLAMA_API_KEY`**; insights sections will show fallback messaging. This is a **server configuration** issue, not something end users fix in the UI.
- **Token / rate limits:** Without **`SOCRATA_APP_TOKEN`**, some CDC requests may fail or throttle; the deployment should set the token via Connect environment variables.

## Related documents

- [`TECHNICAL_DETAILS.md`](TECHNICAL_DETAILS.md) — keys, endpoints, deployment.
- [`SYSTEM_ARCHITECTURE.md`](SYSTEM_ARCHITECTURE.md) — agent and data pipeline overview.
