# Demo script talking points — 3–5 minute website walk-through

Use this while filming: **say the bold “say” lines aloud**, scroll or click **as noted**, and keep **pace ~45–55 seconds per main tab** so the full tour lands in roughly **four minutes** (leave room for pauses).

**TOOL3 rubric (what to land on camera):** **Stakeholder value** (who it helps and why), **clarity** (what to click and in what order), **streamlining** (focused tabs; AI is optional, not clutter), **efficiency** (caching + **Refresh data**), **reliability** (sources load or degrade gracefully), **QC / AI evidence** (optional **Insight quality** expander when `INSIGHT_QC_ENABLED=1`), and **agentic loop** (tools-first pipeline, then parallel analyst → reporter steps—see Overview **Generate insights**). Course brief: [`TOOL3.md`](TOOL3.md).

**Before you roll:** Quiet browser bookmarks bar; zoom Streamlit comfortably; confirm **sidebar load status is green / ok** for NNDSS, kindergarten, wastewater; have **OPENAI_API_KEY** or **OLLAMA_API_KEY** set if you will demo **Generate insights** and AI report buttons. If you will emphasize **quality control**, deploy or local env should have **`INSIGHT_QC_ENABLED=1`** so the **Insight quality rubric** expander appears after **Generate insights**.

**Live deployment (TOOL3):** Use the production build at **https://connect.systems-apps.com/content/b8cfc1fa-8eb0-4c2e-ba98-b5f06837e933/** (same as [`submission_notes.md`](submission_notes.md)).

---

## 0:00–0:25 · Cold open & disclaimer

**On screen:** App title in sidebar, **Overview** selected, sidebar **Data as of** caption visible.

**Say:**
- “This dashboard is for **public-health staff, planners, and anyone tracking U.S. measles risk**—one place to see coverage, cases, and environmental signals together. It’s **situational awareness only**, not clinical or official policy advice. Everything pulls from **CDC-published** datasets.”
- “The **sidebar** is your control panel: **which tab you’re on**, **which feeds succeeded**, and **how fresh the snapshot is**. I’ll walk the main pages top to bottom so you can see the **whole story in under five minutes**.”
- “Runs on our **deployed** Posit Connect build—same URL we submitted—so this isn’t a local-only prototype.”

*(Optional opening line:* “Here’s how we combine vaccination coverage, reported cases, and wastewater signals in one place.”*)*

---

## 0:25–1:10 · Overview

**On screen:** Stay on **Overview**. Point at **Baseline risk** tier, the **gauge**, **Data as of**.

**Say:**
- “**Overview** is the executive snapshot: baseline risk **tier**, a **0–100 meter**, and plain-language summaries—so a new user knows **what matters nationally** in one glance.”
- “Baseline compares **recent national activity** to **historical annual case levels** from the archived CSV—you can read the exact mechanics under **Historical trends**.”
- “We **streamlined** the product around a **small set of tabs**—no duplicate dashboards—and **AI summaries are optional** via **Include AI-written summaries**, so the app stays usable even when LLM keys aren’t configured.”
- “Optional **Generate insights** is our **agentic loop**: **tools pull fresh CDC data first**, then **parallel analyst agents** interpret state vs national context, then **parallel reporters** turn that into readable prose—national always; **state** if you pick **State (optional)**.”
- “It uses alarm probability, baseline, state risk snapshots, and recent weekly case shape so the text stays **grounded in what the app actually computed**.”

**Do:** Optionally expand **Include AI-written summaries**, pick **State (optional)** (e.g. one high-population state), click **Generate insights** once—*only if keys are configured*—then skim the headings so the viewer sees output. **If QC is on:** open the **Insight quality** expander and say one line: “We **score** national and state blurbs on a simple rubric—so we’re not asking anyone to trust the LLM blindly.” **If QC is off:** say briefly that production can turn on **environment-based QC** for validation (see [`TECHNICAL_DETAILS.md`](TECHNICAL_DETAILS.md)).

---

## 1:10–1:55 · Historical trends

**On screen:** Radio → **Historical trends**.

**Say:**
- “This tab backs the headline numbers with **trend charts**.”
- “You get **annual national cases** from the historical CSV, and **weekly NNDSS** national totals—the same weekly series the rest of the app uses.”
- “The **expanders** spell out **how alarm probability is built**—features like recent cases, wastewater trend, kindergarten coverage, seasonality—and **how baseline tier and score relate** to recent vs long-run averages.”

**Do:** Briefly toggle **NNDSS weekly view** (e.g. “Last 104 weeks” vs a single year); mention **Download summary metrics as CSV** for reproducibility—no need to download on camera unless you want a beat.

---

## 1:55–2:40 · Kindergarten coverage

**On screen:** **Kindergarten coverage**.

**Say:**
- “**Kindergarten MMR coverage by state**—darker blues on the map mean **higher coverage**; gaps show **data unavailable** for some jurisdictions.”
- “We filter by **school year** when the dataset provides it—that keeps the choropleth and table aligned with what CDC reported for that assessment cycle.”
- “Low coverage raises **risk in the modeling and state composite** downstream; here it’s easiest to spot geographically.”

**Do:** Change **Select coverage year** once to show the map and table update.

---

## 2:40–3:30 · Wastewater vs NNDSS

**On screen:** **Wastewater vs NNDSS**.

**Say:**
- “This pairs **measles wastewater detection frequency**—*share of reporting sites detecting RNA*, not patient counts—with **weekly NNDSS case counts** on a dual-axis chart.”
- “Filtering **From year / To year** trims both series; wastewater only exists where CDC surveillance runs, so older years might be **cases-only**.”
- “Optional **Generate AI report** summarizes the last few weeks’ trend—it reminds viewers that **correlation isn’t causation** and mentions reporting lag.”

**Do:** Point at latest-week **percentage of sites** line; widen or narrow years once to show chart behavior.

---

## 3:30–4:15 · State risk

**On screen:** **State risk**.

**Say:**
- “**State-level risk** combines **coverage pressure**, recent **reported-case activity**, and **wastewater signal** where the state participates—scores roll into tiers that split states into thirds on this **run**, so treat tiers as situational grouping, not hard cutoffs.”
- “Table columns show **recent cases**, **wastewater signal**, and whether the state had **monitoring coverage** in the wastewater feed.”

**Do:** Hover map briefly; optionally open **How state risk is calculated** expander without reading every bullet; pick a state under **Generate AI report for this state** and click generate *if demonstrating AI*.

---

## 4:15–5:00 · Forecast & close

**On screen:** **Forecast**.

**Say:**
- “**Forecast by state** reuses those same state scores to assign a simple **outlook word**—High, Watch, or Low—and points to **what’s driving it**—coverage, recent cases, or wastewater.”
- “When the short-term projection model succeeds, we show a compact **national next-few-weeks expectation** caption as well.”
- “Again, **Generate AI interpretation** summarizes the tableau in plain English for stakeholders—for that you’d need API keys wired in Posit Connect or locally.”

**Closing line:** “Together: **baseline snapshot**, drill-down **history**, **geography**, **near-real environmental signal**, **per-state composites**, and a **forecast readout**, all anchored on published CDC feeds and clearly labeled limitations—that’s the **stakeholder story** end to end.”

**On screen:** Return to sidebar; hit **efficiency / reliability** on the way out:

**Say (pick one short beat):**
- “**Caching** keeps repeat visits responsive; **Refresh data** forces a new pull when you care about the latest CDC drop.”
- “If a feed fails, the **sidebar tells you**—the app **doesn’t pretend** missing data is zero.”

**Then:** Optional **Refresh data** nod: “Refreshing re-fetches upstream when you need to clear cache.” Cut.

---

## Quick reference — must-hit list

| Beat | Viewer takeaway | Rubric hook (TOOL3) |
|------|-----------------|---------------------|
| Sidebar | Loads, timestamps, disclaimers | **Clarity**, **reliability** |
| Overview | Tier + gauge + optional agent insights | **Stakeholder alignment**, **clarity**, **agentic loop** |
| Insight quality (if enabled) | Scores / rubric after **Generate insights** | **QC**, **evidence of AI performance** |
| Historical | Weekly + annual + methodology expanders | **Clarity**, **reliability** of methodology |
| Kindergarten | Year filter + national map semantics | **Stakeholder** geography |
| Wastewater vs NNDSS | Share-of-sites vs cases; year filters | **Streamlining** one comparison view |
| State risk | Map + composite + optional state AI | **Stakeholder** state prioritization |
| Forecast | Outlook + drivers + optional national caption + AI | **Reliability** of consistent scoring |
| Deployed URL | Same Connect link as submission | **Working deployed link** |
| Refresh / cache | Mention once | **Efficiency** |

---

## Fallback if something fails live

**Say:** “One source is flagged **unavailable** in the sidebar—that’s expected on a bad token or outage; charts that depend on it **degrade gracefully** instead of inventing numbers.” That directly supports the rubric’s **reliability** question: the app **does what it promises** about data honesty.

Do not troubleshoot on camera unless the video is intentionally a debug session.
