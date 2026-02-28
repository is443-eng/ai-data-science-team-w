# Predictive Measles Risk Dashboard

A **Streamlit** dashboard that combines **historical measles data**, **kindergarten MMR vaccination coverage**, **CDC wastewater**, and **NNDSS** case data to compute **baseline risk**, **outbreak alarm probability**, **state-level risk**, and **short-term case forecast**. It uses a two-stage **Alarm–then–Forecast** model and optional **Ollama Cloud** AI for plain-language interpretation.

**Disclaimer:** For situational awareness only; not for clinical or policy decisions. Data: CDC.

---

## What the app does

| Feature | Description |
|--------|-------------|
| **Overview** | Outbreak alarm probability (next 4 weeks), baseline risk tier and 0–100 gauge, national case forecast; coefficient drivers; optional AI summary; download CSV. |
| **Historical trends** | National annual measles cases (CSV) and NNDSS weekly cases (last 104 weeks, all weeks, or by year). |
| **Kindergarten coverage** | MMR coverage by state (map + table), year selector; links low coverage to outbreak risk. |
| **Wastewater vs NNDSS** | Dual-axis chart: wastewater detection frequency (% of sites) vs NNDSS weekly cases; year filters; data audit; optional AI report comparing trends. |
| **State risk** | Choropleth and table: recent cases, wastewater signal (or “No coverage”), wastewater coverage (Yes/No), final score; tiers High/Medium/Low; per-state AI report. |
| **Forecast** | State outlook (High / Watch / Low) and drivers; national 4-week case expectation; AI interpretation with hotspots, precautions, and CDC link. |

See **[DOCUMENTATION.md](DOCUMENTATION.md)** for architecture diagrams, data flow, risk formulas, and file layout.

---

## Dependencies

Install from project root:

```bash
pip install -r dashboard/requirements.txt
```

| Package | Min version | Purpose |
|---------|-------------|---------|
| streamlit | 1.28.0 | Web UI |
| pandas | 1.5.0 | Data handling |
| numpy | 1.21.0 | Numerics |
| requests | 2.28.0 | CDC Socrata + Ollama APIs |
| python-dotenv | 1.0.0 | `.env` (tokens) |
| plotly | 5.14.0 | Charts |
| scikit-learn | 1.2.0 | Alarm model (logistic regression) |

**Python:** 3.9+ recommended.

---

## Prerequisites

- **Python 3.9+**
- **`.env`** at the **project root** (parent of `dashboard/`) with:
  - **`SOCRATA_APP_TOKEN`** — required for CDC Socrata (kindergarten, wastewater, NNDSS). Without it, only the historical CSV may load.
  - **`OLLAMA_API_KEY`** — optional; needed for all “Generate AI…” buttons. App runs without it; AI sections will show an error message.

---

## Run

From the **project root** (so that `dashboard` imports resolve):

```bash
cd /path/to/ai-data-science-team-w
PYTHONPATH=. streamlit run dashboard/app.py
```

One-liner (replace with your path):

```bash
cd /path/to/ai-data-science-team-w && PYTHONPATH=. streamlit run dashboard/app.py
```

Optional script (if present):

```bash
./run_dashboard.sh
```

Then open the URL shown in the terminal (e.g. **http://localhost:8501**).

---

## Environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| `SOCRATA_APP_TOKEN` | Yes (for live CDC data) | CDC Socrata app token. Get one at [CDC Socrata](https://data.cdc.gov/). |
| `OLLAMA_API_KEY` | No | Ollama Cloud API key for AI summaries and reports. |

---

## Logs and troubleshooting

- **Log file:** `dashboard/dashboard.log`. Logs go to file and console; no API keys or PII.
- **Load failed:** Ensure `.env` is at the project root and contains `SOCRATA_APP_TOKEN`. Check CDC API status if all sources fail.
- **Kindergarten / Wastewater / NNDSS: temporarily unavailable:** That source failed (network, rate limit, or API change). Other pages still work.
- **Forecast or state risk missing:** Load kindergarten and NNDSS, then click **Refresh data**.
- **AI summary/report unavailable:** Set `OLLAMA_API_KEY` in `.env` or check network/timeout; see `dashboard.log`.

---

## Documentation

- **[DOCUMENTATION.md](DOCUMENTATION.md)** — Architecture, data flow diagrams, data sources, risk model (alarm, forecast, baseline, state risk), UI pages, AI integration, dependencies, file layout, env vars, and error handling.
