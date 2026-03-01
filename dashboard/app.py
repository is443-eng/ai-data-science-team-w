"""
Risk of Measles Outbreak in US — Streamlit entrypoint.
Loads data, runs alarm model, shows Overview, Historical, Kindergarten,
Wastewater vs NNDSS (detection frequency), State risk, and Forecast. Reads .env from project root.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Add project root for imports when running as streamlit run dashboard/app.py
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import numpy as np
import pandas as pd
import streamlit as st

from dashboard.utils.logging_config import setup_logging, get_logger

setup_logging()
logger = get_logger("app")

# Page config
st.set_page_config(page_title="Risk of Measles Outbreak in US", page_icon="📊", layout="wide")

# Session state for cached data and model
if "load_status" not in st.session_state:
    st.session_state.load_status = {}
if "data_as_of" not in st.session_state:
    st.session_state.data_as_of = ""
if "alarm_prob" not in st.session_state:
    st.session_state.alarm_prob = 0.5
if "ollama_summary" not in st.session_state:
    st.session_state.ollama_summary = None
if "nndss_agg" not in st.session_state:
    st.session_state.nndss_agg = None
if "nndss_audit" not in st.session_state:
    st.session_state.nndss_audit = {}
if "model_stage1" not in st.session_state:
    st.session_state.model_stage1 = None
if "coef_df" not in st.session_state:
    st.session_state.coef_df = None


def load_and_model(use_cache: bool = True, outbreak_threshold: float = 0):
    from dashboard.loaders import load_all, clear_cache
    from dashboard.risk import (
        fit_stage1,
        predict_alarm_probability,
        get_forecast,
        get_baseline_risk,
        get_state_risk_df,
    )
    if not use_cache:
        clear_cache()
    hist, kg, ww, nndss, load_status, data_as_of = load_all(use_cache=use_cache)
    st.session_state.load_status = load_status
    st.session_state.data_as_of = data_as_of
    st.session_state.hist = hist
    st.session_state.kg = kg
    st.session_state.ww = ww
    st.session_state.nndss = nndss
    # Single canonical NNDSS national weekly aggregation for all tabs
    from dashboard.risk import get_national_weekly_cases
    nndss_agg, nndss_audit = get_national_weekly_cases(nndss) if (nndss is not None and not nndss.empty) else (pd.DataFrame(), {})
    st.session_state.nndss_agg = nndss_agg
    st.session_state.nndss_audit = nndss_audit
    if not nndss_agg.empty:
        recent = nndss_agg.tail(5)
        logger.info("Five most recent NNDSS (national weekly cases) available to app: %s", recent[["year", "week", "cases"]].to_dict("records"))
    try:
        model, coef_df, auc, _ = fit_stage1(nndss, ww, kg, outbreak_threshold=outbreak_threshold)
        st.session_state.model_stage1 = model
        st.session_state.coef_df = coef_df
        st.session_state.auc = auc
        st.session_state.alarm_prob = predict_alarm_probability(model, nndss, ww, kg, outbreak_threshold)
    except Exception as e:
        logger.exception("Stage 1 fit/predict failed")
        st.session_state.alarm_prob = 0.5
        st.session_state.model_stage1 = None
        st.session_state.coef_df = None
    try:
        forecast_df, ok = get_forecast(nndss)
        st.session_state.forecast_df = forecast_df if ok else None
    except Exception:
        st.session_state.forecast_df = None
    try:
        baseline_tier, baseline_val = get_baseline_risk(hist, nndss)
        st.session_state.baseline_tier = baseline_tier
        st.session_state.baseline_val = baseline_val
    except Exception:
        st.session_state.baseline_tier = "low"
        st.session_state.baseline_val = 0.0
    try:
        st.session_state.state_risk_df = get_state_risk_df(kg, nndss, ww)
    except Exception:
        st.session_state.state_risk_df = None
    return hist, kg, ww, nndss


def _render_main(page: str) -> None:
    hist = st.session_state.get("hist")
    kg = st.session_state.get("kg")
    ww = st.session_state.get("ww")
    nndss = st.session_state.get("nndss")

    if not st.session_state.get("data_loaded", False):
        st.warning("Data could not be loaded. Set SOCRATA_APP_TOKEN in .env and try again.")
        st.stop()
        return

    # Disclaimer
    st.caption("For situational awareness only; not for clinical or policy decisions. Data: CDC.")

    if page == "Overview":
        st.header("Risk of Measles Outbreak in US")
        st.caption("Key risk metrics at a glance.")
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Outbreak alarm", f"{st.session_state.get('alarm_prob', 0.5):.0%}",
                      help="Probability that reported cases will exceed the threshold in the next 4 weeks.")
        with c2:
            st.metric("Baseline risk", st.session_state.get("baseline_tier", "low").upper(),
                      help="Low / medium / high compared to past years.")
        with c3:
            st.metric("Risk score (0–100)", f"{st.session_state.get('baseline_val', 0):.0f}",
                      help="Higher = more concern based on recent vs historical cases.")
        baseline_val = float(st.session_state.get("baseline_val", 0))
        import plotly.graph_objects as go
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=baseline_val,
            number={"suffix": ""},
            title={"text": "Baseline risk meter"},
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color": "darkgray"},
                "steps": [
                    {"range": [0, 33], "color": "lightgreen"},
                    {"range": [33, 67], "color": "lightyellow"},
                    {"range": [67, 100], "color": "lightcoral"},
                ],
                "threshold": {"line": {"color": "black", "width": 2}, "value": baseline_val},
            },
        ))
        fig_gauge.update_layout(height=180, margin=dict(l=40, r=40, t=50, b=30))
        st.plotly_chart(fig_gauge, use_container_width=True)
        with st.expander("How is alarm probability calculated?", expanded=False):
            st.markdown("**Inputs used:** Recent national cases, wastewater trend (prior 8–12 weeks of detection data), kindergarten MMR coverage (national), and week of year (seasonality).")
            coef_df = st.session_state.get("coef_df")
            if coef_df is not None and not coef_df.empty:
                pos = coef_df[coef_df["coefficient"] > 0].sort_values("coefficient", ascending=False)
                neg = coef_df[coef_df["coefficient"] < 0].sort_values("coefficient", ascending=True)
                if not pos.empty:
                    st.markdown("**Top positive drivers** (push alarm up): " + ", ".join([f"{r['feature']} ({r['coefficient']:.2f})" for _, r in pos.head(3).iterrows()]) + ".")
                if not neg.empty:
                    st.markdown("**Top negative drivers** (push alarm down): " + ", ".join([f"{r['feature']} ({r['coefficient']:.2f})" for _, r in neg.head(3).iterrows()]) + ".")
                st.caption("Coefficients (positive = increases probability, negative = decreases):")
                st.dataframe(coef_df, use_container_width=True, hide_index=True)
            st.markdown(
                "**Plain language:** Risk increases when recent wastewater levels are higher, when kindergarten coverage is lower, "
                "or when the time of year is typically associated with more cases. The model combines these into a single probability."
            )
        with st.expander("How is baseline risk/score calculated?", expanded=False):
            from dashboard.risk import get_baseline_risk_components
            comp = get_baseline_risk_components(
                hist if hist is not None else pd.DataFrame(),
                nndss if nndss is not None else pd.DataFrame(),
            )
            st.markdown("**Inputs used:** Historical national annual cases (CSV) and recent NNDSS weekly national cases.")
            st.markdown(
                "**Baseline risk** compares **recent** measles case levels to **historical** (annual national cases from the CSV). "
                "We take the **average of the last 5 years** and the **overall average**; the **ratio** (recent ÷ overall) determines the tier and score."
            )
            st.caption(f"Recent 5-year average: **{comp.get('recent_5yr_avg', '—')}**. Overall average: **{comp.get('overall_avg', '—')}**. Ratio: **{comp.get('ratio', '—')}**.")
            if comp.get("formula"):
                st.caption(comp["formula"])
            st.markdown("**Plain language:** Higher recent case levels relative to history mean a higher baseline score and medium or high tier.")
        st.caption("See the **Forecast** tab for state-level outlook.")
        # Export
        import io
        import csv
        rows = [
            ["metric", "value"],
            ["alarm_probability", st.session_state.get("alarm_prob", 0.5)],
            ["baseline_tier", st.session_state.get("baseline_tier", "")],
            ["baseline_score", st.session_state.get("baseline_val", 0)],
            ["data_as_of", st.session_state.get("data_as_of", "")],
        ]
        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerows(rows)
        st.download_button("Download summary as CSV", buf.getvalue(), file_name="overview_summary.csv", mime="text/csv", key="dl_overview")

    elif page == "Historical trends":
        st.header("Historical trends")
        if hist is not None and not hist.empty:
            case_col = "Measles Cases" if "Measles Cases" in hist.columns else hist.columns[1]
            import plotly.express as px
            fig = px.line(hist, x=hist.columns[0], y=case_col, title="National annual measles cases (historical CSV)")
            st.plotly_chart(fig, width="stretch")
        else:
            st.warning("No historical data.")
        # Use canonical NNDSS national weekly aggregation (same as all tabs)
        nndss_agg = st.session_state.get("nndss_agg")
        nndss_audit = st.session_state.get("nndss_audit", {})
        if (nndss_agg is None or (isinstance(nndss_agg, pd.DataFrame) and nndss_agg.empty)) and nndss is not None and not nndss.empty:
            from dashboard.risk import get_national_weekly_cases
            nndss_agg, nndss_audit = get_national_weekly_cases(nndss)
        if nndss is not None and not nndss.empty and (nndss_agg is None or (isinstance(nndss_agg, pd.DataFrame) and nndss_agg.empty)):
            top10 = nndss_audit.get("columns_available_top10") if nndss_audit else list(nndss.columns)[:10]
            st.warning("**No expected NNDSS case column found.** Adjust code to use one of these columns. Top 10 column names: **%s**" % (top10,))
        if nndss_agg is not None and not nndss_agg.empty:
            nndss_agg_copy = nndss_agg.copy()
            nndss_agg_copy["year"] = pd.to_numeric(nndss_agg_copy["year"], errors="coerce")
            years_in_agg = sorted(nndss_agg_copy["year"].dropna().astype(int).unique().tolist())
            view_options = ["Last 104 weeks", "All available weeks"] + [str(y) for y in years_in_agg]
            view_choice = st.selectbox("NNDSS weekly view", view_options, index=0, key="nndss_view")
            if view_choice == "Last 104 weeks":
                agg = nndss_agg_copy.tail(104).copy()
            elif view_choice == "All available weeks":
                agg = nndss_agg_copy.copy()
            else:
                y = int(view_choice)
                agg = nndss_agg_copy[nndss_agg_copy["year"].astype(int) == y].copy()
                agg = agg.sort_values(["year", "week"]).reset_index(drop=True)
            agg["year_week"] = agg["year"].astype(int).astype(str) + "-W" + agg["week"].astype(int).apply(lambda x: str(x).zfill(2))
            import plotly.express as px
            fig2 = px.line(agg, x="year_week", y="cases", title="National weekly cases (NNDSS)")
            fig2.update_layout(xaxis_title="Week ending", yaxis_title="Reported measles cases (weekly)", height=400)
            st.plotly_chart(fig2, width="stretch")
            recent5 = agg[["year", "week", "cases"]].tail(5).copy()
            recent5["Year-Week"] = recent5["year"].astype(int).astype(str) + "-W" + recent5["week"].astype(int).apply(lambda x: str(x).zfill(2))
            st.caption("**Five most recent NNDSS cases (national weekly) available to this app:**")
            st.dataframe(recent5[["Year-Week", "cases"]].rename(columns={"cases": "Cases"}), use_container_width=True, hide_index=True)
        with st.expander("NNDSS data audit", expanded=False):
            if nndss_audit:
                st.write("**Case column used:**", nndss_audit.get("case_column_used"), "| **Year range:**", nndss_audit.get("year_min"), "–", nndss_audit.get("year_max"), "| **Most recent (year, week):**", nndss_audit.get("year_week_max"))
                st.write("**National rows before agg:**", nndss_audit.get("n_national_rows"), "| **year_max before agg:**", nndss_audit.get("year_max_before_agg"), "| **year_max after agg:**", nndss_audit.get("year_max_after_agg"))
                if nndss_audit.get("candidate_case_columns"):
                    st.write("**Candidate case columns (non-null %):**", nndss_audit.get("candidate_case_columns"))
            else:
                st.write("No NNDSS national weekly data (empty or not loaded).")

    elif page == "Kindergarten coverage":
        st.header("Kindergarten MMR vaccination coverage by state")
        if kg is not None and not kg.empty:
            state_col = next((c for c in ["state", "State", "jurisdiction", "geography", "location1"] if c in kg.columns), kg.columns[0])
            pct_col = next((c for c in kg.columns if "pct" in c.lower() or "coverage" in c.lower()), kg.columns[1] if len(kg.columns) > 1 else None)
            kg_full = kg.copy()
            year_options = []
            year_source = None
            if "_year_derived" in kg_full.columns and "_year_source" in kg_full.columns:
                # Use loader-derived year (from explicit column or regex/single-year)
                year_source = kg_full["_year_source"].iloc[0] if kg_full["_year_source"].notna().any() else None
                valid = kg_full["_year_derived"].notna() & (pd.to_numeric(kg_full["_year_derived"], errors="coerce") >= 2000) & (pd.to_numeric(kg_full["_year_derived"], errors="coerce") < 2100)
                year_options = sorted(pd.to_numeric(kg_full.loc[valid, "_year_derived"], errors="coerce").dropna().astype(int).unique().tolist())
            if not year_options:
                year_col = next((c for c in ["school_year", "reporting_year", "year", "school year", "coverage_school_year"] if c in kg.columns), None)
                if not year_col:
                    year_col = next((c for c in kg.columns if "year" in c.lower() or "school" in c.lower()), None)
                if year_col:
                    raw = kg_full[year_col].astype(str).str.strip()
                    kg_full["_year"] = pd.to_numeric(raw, errors="coerce")
                    valid = kg_full["_year"].notna() & (kg_full["_year"] >= 2000) & (kg_full["_year"] < 2100)
                    kg_full["_year_key"] = np.nan
                    kg_full.loc[valid, "_year_key"] = kg_full.loc[valid, "_year"].astype(int)
                    year_options = sorted(kg_full["_year_key"].dropna().unique().astype(int).tolist())
                    year_source = year_col
            if year_options:
                if len(year_options) == 1 and year_source == "single_year":
                    st.info("Dataset contains a single year: **%s**" % year_options[0])
                selected_year = st.selectbox("Select coverage year (map and table show this year only)", year_options, index=len(year_options) - 1, format_func=lambda x: str(int(x)), key="kg_year")
                if "_year_derived" in kg_full.columns:
                    kg_work = kg_full[pd.to_numeric(kg_full["_year_derived"], errors="coerce") == selected_year].copy()
                else:
                    kg_work = kg_full[kg_full["_year_key"] == selected_year].copy()
                st.subheader(f"Coverage year: {selected_year}")
                if kg_work.empty:
                    st.warning("**0 rows after filters.** Year selected: %s. No kindergarten data for this year." % selected_year)
            else:
                selected_year = None
                kg_work = kg_full
                st.subheader("Coverage year: (all years — no year column found in data)")
            with st.expander("Kindergarten data audit", expanded=False):
                st.write("**Year source:**", year_source if year_source else "none (no year column or derived year)")
                if "_year_derived" in kg_full.columns:
                    st.write("**Derived year logic:**", kg_full["_year_source"].iloc[0] if kg_full["_year_source"].notna().any() else "—")
                    st.write("**Available years:**", sorted(pd.to_numeric(kg_full["_year_derived"], errors="coerce").dropna().astype(int).unique().tolist()) if kg_full["_year_derived"].notna().any() else "—")
            st.caption("Lower coverage in a state is linked to higher outbreak risk. Data: CDC school vaccination assessments.")
            if pct_col and not kg_work.empty:
                kg_work["coverage"] = pd.to_numeric(kg_work[pct_col], errors="coerce")
                cov_agg = kg_work.groupby(state_col, as_index=False)["coverage"].mean()
                cov_agg = cov_agg.dropna(subset=["coverage"])
                from dashboard.utils.state_maps import state_to_abbr
                cov_agg["abbr"] = cov_agg[state_col].astype(str).apply(state_to_abbr)
                cov_map = cov_agg.dropna(subset=["abbr"])
                if not cov_map.empty:
                    import plotly.express as px
                    fig_map = px.choropleth(
                        cov_map, locations="abbr", locationmode="USA-states",
                        color="coverage", scope="usa",
                        color_continuous_scale="Blues",
                        title="MMR coverage % by state (darker = higher coverage)",
                    )
                    fig_map.update_layout(height=400)
                    st.plotly_chart(fig_map, width="stretch")
                table_df = cov_agg[[state_col, "coverage"]].rename(columns={state_col: "State", "coverage": "Percent coverage"})
                st.dataframe(table_df, use_container_width=True, hide_index=True)
            else:
                st.info("No coverage data for selected filters.")
        else:
            st.info("No kindergarten data.")

    elif page == "Wastewater vs NNDSS":
        st.header("Wastewater vs NNDSS: detection frequency")
        from dashboard.risk import (
            compute_ww_detection_frequency,
            validate_ww_nndss_audit,
        )
        nndss_agg = st.session_state.get("nndss_agg")
        if nndss_agg is None:
            nndss_agg = pd.DataFrame()
        if not nndss_agg.empty:
            nndss_agg = nndss_agg.copy()
            nndss_agg["year"] = pd.to_numeric(nndss_agg["year"], errors="coerce")
            nndss_agg = nndss_agg.dropna(subset=["year"])
            nndss_agg["year"] = nndss_agg["year"].astype(int)
            years_avail = sorted(nndss_agg["year"].unique().tolist())
        else:
            years_avail = []
        if ww is not None and not ww.empty and "year" in ww.columns:
            ww_years = sorted(pd.to_numeric(ww["year"], errors="coerce").dropna().astype(int).unique().tolist())
            years_avail = sorted(set(years_avail) | set(ww_years)) if years_avail else ww_years
        # Get wastewater availability range for UI message (no year filter)
        _, ww_val_range = compute_ww_detection_frequency(ww if ww is not None else pd.DataFrame(), year_min=None, year_max=None)
        weeks_min = ww_val_range.get("weeks_min")
        weeks_max = ww_val_range.get("weeks_max")
        ww_year_min = int(weeks_min[0]) if weeks_min else None
        ww_year_max = int(weeks_max[0]) if weeks_max else None
        if ww_year_min is not None and ww_year_max is not None:
            st.info(
                f"Wastewater measles surveillance is available from **{ww_year_min}** through **{ww_year_max}**. "
                "Years before this period will not display wastewater data."
            )
        year_min, year_max = None, None
        if years_avail:
            year_min = st.selectbox("From year", [None] + years_avail, format_func=lambda x: "All" if x is None else str(x), key="ww_year_min")
            year_max = st.selectbox("To year", [None] + years_avail, index=len(years_avail), format_func=lambda x: "All" if x is None else str(x), key="ww_year_max")
            st.caption("Wastewater availability may limit the earliest year shown. See audit below for start date.")
        ww_weekly, ww_val = compute_ww_detection_frequency(ww if ww is not None else pd.DataFrame(), year_min=year_min, year_max=year_max)
        nndss_filtered = nndss_agg.copy()
        if not nndss_filtered.empty:
            if year_min is not None:
                nndss_filtered = nndss_filtered[nndss_filtered["year"].astype(int) >= int(year_min)]
            if year_max is not None:
                nndss_filtered = nndss_filtered[nndss_filtered["year"].astype(int) <= int(year_max)]
        audit = validate_ww_nndss_audit(ww_val, ww_weekly, nndss_filtered, year_min, year_max)
        nndss_sum = audit.get("nndss_cases_sum", 0)
        if nndss_sum == 0 and not nndss_filtered.empty:
            st.warning(
                "**NNDSS cases sum for selected period: 0.** "
                "Filters used: %s. No reported measles cases in this window; charts may be empty."
                % audit.get("nndss_window", "year range")
            )
        if ww_weekly.empty and ww is not None and not ww.empty:
            st.warning(
                "**0 rows after filters.** Wastewater QC filters applied: pcr_target = measles (MEV/Measles virus), ntc_amplify = no, (inhibition_detect = no OR inhibition_adjust = yes). "
                "Year range: From=%s To=%s. Raw rows loaded: %s."
                % (year_min, year_max, ww_val.get("n_rows_raw", 0))
            )
        if ww_year_min is not None and year_max is not None and int(year_max) < ww_year_min:
            st.warning("No wastewater data available for the selected years. Measles wastewater monitoring began in **%s**." % ww_year_min)
        with st.expander("Wastewater data audit", expanded=False):
            missing = ww_val.get("missing_columns")
            if missing:
                st.warning("**Required column(s) missing:** %s. **Columns present:** %s" % (missing, ww_val.get("columns_present")))
            st.write("**Detection rule:**", ww_val.get("detection_rule_used") or "—")
            st.write("**Rows before filters:**", ww_val.get("n_rows_raw", 0))
            st.write("**% passing QC:**", "%.1f" % ww_val.get("pct_passing_qc", 0), "%")
            st.write("**Unique sites:**", ww_val.get("n_unique_sites", 0))
            wmin, wmax = ww_val.get("weeks_min"), ww_val.get("weeks_max")
            st.write("**Wastewater starts:**", wmin, "| **ends:**", wmax)
            if not ww_weekly.empty:
                st.write("**Wastewater year range:**", int(ww_weekly["year"].min()), "–", int(ww_weekly["year"].max()))
            st.write("**pcr_target used:**", ww_val.get("pcr_target_used"))
        if not ww_weekly.empty:
            latest = ww_weekly.sort_values(["year", "week"], ascending=[False, False]).iloc[0]
            pct = 100 * latest["detection_frequency"] if latest["total_sites"] else 0
            st.markdown("**This week (latest in data):** %.0f%% of reporting wastewater sites detected measles RNA." % pct)
        if not ww_weekly.empty or not nndss_filtered.empty:
            if not ww_weekly.empty and not nndss_filtered.empty:
                merged_inner = ww_weekly.copy()
                merged_inner["year"] = merged_inner["year"].astype(int)
                nndss_f = nndss_filtered.copy()
                nndss_f["year"] = nndss_f["year"].astype(int)
                merged_inner = merged_inner.merge(nndss_f[["year", "week", "cases"]], on=["year", "week"], how="inner")
                if merged_inner.empty:
                    st.warning(
                        "**No overlapping wastewater + NNDSS weeks for selected year range.** "
                        "Wastewater and NNDSS have no common (year, week) keys. Showing no plot to avoid misleading zeros. "
                        "Check the Merge keys audit expander for each series’ year range and last (year, week)."
                    )
                else:
                    merged_inner = merged_inner.sort_values(["year", "week"]).reset_index(drop=True)
                    merged_inner["year_week"] = merged_inner["year"].astype(str) + "-W" + merged_inner["week"].astype(int).astype(str)
                    import plotly.graph_objects as go
                    fig = go.Figure()
                    fig.add_trace(go.Scatter(x=merged_inner["year_week"], y=merged_inner["detection_frequency"].values, name="Detection frequency (share of sites)", line=dict(color="steelblue", width=2), mode="lines+markers", marker=dict(size=4)))
                    fig.add_trace(go.Scatter(x=merged_inner["year_week"], y=merged_inner["cases"].values, name="Reported cases (NNDSS)", yaxis="y2", line=dict(color="darkorange", width=2), mode="lines+markers", marker=dict(size=4)))
                    fig.update_layout(
                        height=480,
                        font=dict(size=12),
                        yaxis=dict(title="Detection frequency (share of sites)", tickformat=".0%"),
                        yaxis2=dict(overlaying="y", side="right", title="Reported measles cases (weekly)"),
                        title="Wastewater detection frequency vs NNDSS cases",
                        xaxis=dict(title="Week", type="category", tickangle=-45),
                        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                    )
                    st.plotly_chart(fig, width="stretch", use_container_width=True)
        # AI Reporter: Wastewater vs NNDSS
        st.subheader("AI Reporter: Wastewater vs NNDSS")
        ww_nndss_summary_parts = []
        if not ww_weekly.empty:
            last8_ww = ww_weekly.sort_values(["year", "week"], ascending=[False, False]).head(8)
            if not last8_ww.empty:
                freq = last8_ww["detection_frequency"].values
                mn, mx = float(freq.min()), float(freq.max())
                last_val = float(freq[0])
                direction_ww = "up" if len(freq) >= 2 and freq[0] > freq[-1] else ("down" if len(freq) >= 2 and freq[0] < freq[-1] else "flat")
                ww_nndss_summary_parts.append("Wastewater detection_frequency (last 8 weeks): min=%.2f, max=%.2f, latest=%.2f (share of sites); trend %s." % (mn, mx, last_val, direction_ww))
        if not nndss_filtered.empty:
            last8_nd = nndss_filtered.sort_values(["year", "week"], ascending=[False, False]).head(8)
            if not last8_nd.empty:
                cases = last8_nd["cases"].values
                mn, mx = int(cases.min()), int(cases.max())
                last_c = int(cases[0])
                direction_nd = "up" if len(cases) >= 2 and cases[0] > cases[-1] else ("down" if len(cases) >= 2 and cases[0] < cases[-1] else "flat")
                ww_nndss_summary_parts.append("NNDSS cases (last 8 weeks): min=%s, max=%s, latest=%s; trend %s." % (mn, mx, last_c, direction_nd))
        wmin, wmax = ww_val.get("weeks_min"), ww_val.get("weeks_max")
        if wmin is not None or wmax is not None:
            ww_nndss_summary_parts.append("Wastewater data availability: weeks %s to %s." % (wmin or "?", wmax or "?"))
        ww_nndss_summary_text = " ".join(ww_nndss_summary_parts) if ww_nndss_summary_parts else "No summary data available."
        data_as_of_ww = st.session_state.get("data_as_of", "")
        if st.button("Generate AI report", key="btn_ww_nndss_report"):
            from dashboard.ollama_client import get_ollama_ww_nndss_report
            report = get_ollama_ww_nndss_report(ww_nndss_summary_text, data_as_of_ww)
            st.session_state.ww_nndss_ai_report = report or "Could not generate (add OLLAMA_API_KEY to .env or check dashboard.log)."
        if st.session_state.get("ww_nndss_ai_report"):
            st.markdown(st.session_state.ww_nndss_ai_report)
        st.caption("Compares wastewater detection trend vs NNDSS cases; interprets lead time and cautions (correlation ≠ causation, reporting delays). Requires **OLLAMA_API_KEY** in `.env`.")
        with st.expander("AI Reporter: understanding wastewater detection", expanded=False):
            st.markdown("- **Detection frequency** = share of reporting wastewater sites that had measurable measles RNA in that week. It is *not* a count of patients or cases.")
            st.markdown("- **Why it matters:** When more sites detect virus, community circulation may be higher; it can sometimes appear in wastewater before confirmed cases are reported.")
            st.markdown("- **How to interpret:** An *increase* in detection frequency suggests more sites seeing virus; a *decrease* may mean less circulation or fewer sites reporting.")
            st.markdown("- **Lag correlation:** A positive correlation at lag K means detection frequency K weeks ago lines up with cases this week. Correlation does not prove causation; reporting and lab delays affect timing.")
        if not nndss_filtered.empty and ww_weekly.empty:
            merged = nndss_filtered.sort_values(["year", "week"])
            merged["year_week"] = merged["year"].astype(str) + "-W" + merged["week"].astype(str)
            import plotly.graph_objects as go
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=merged["year_week"], y=merged["cases"], name="Reported cases (NNDSS)", mode="lines+markers"))
            fig.update_layout(title="Reported cases by week (no wastewater detection data in selected period)")
            st.plotly_chart(fig, width="stretch")
        if not ww_weekly.empty and nndss_filtered.empty:
            st.info("NNDSS has no data in selected window; only detection frequency is shown above.")
        if ww_weekly.empty and nndss_filtered.empty and (year_min is not None or year_max is not None):
            st.warning("No data for the selected year range. Try \"All\" for From year or To year to see full range.")

    elif page == "State risk":
        st.header("State-level risk")
        st.caption("Risk tier and score by state (coverage, recent cases, wastewater where available).")
        sr = st.session_state.get("state_risk_df")
        if sr is not None and not sr.empty:
            from dashboard.utils.state_maps import state_to_abbr
            sr = sr.copy()
            sr["abbr"] = sr["state"].apply(state_to_abbr)
            sr_map = sr.dropna(subset=["abbr"])
            if not sr_map.empty:
                import plotly.express as px
                fig_sr = px.choropleth(
                    sr_map, locations="abbr", locationmode="USA-states",
                    color="risk_score", scope="usa",
                    color_continuous_scale="Blues",
                    title="Risk score by state (darker blue = higher concern)",
                )
                fig_sr.update_layout(height=400)
                st.plotly_chart(fig_sr, width="stretch")
            display_cols = ["state", "cases_recent", "ww_recent", "wastewater_coverage", "total_risk"]
            if not all(c in sr.columns for c in display_cols):
                display_cols = ["state", "cases_recent", "ww_recent", "total_risk"]
            if all(c in sr.columns for c in display_cols):
                tbl = sr[display_cols].copy()
                tbl["Wastewater signal"] = tbl["ww_recent"].apply(lambda x: "No coverage" if (x is None or (isinstance(x, float) and pd.isna(x))) else (round(x, 4) if isinstance(x, (int, float)) else x))
                if "wastewater_coverage" in tbl.columns:
                    tbl["Wastewater coverage"] = tbl["wastewater_coverage"].map({True: "Yes", False: "No"})
                show_cols = ["state", "cases_recent", "Wastewater signal"] + (["Wastewater coverage"] if "wastewater_coverage" in tbl.columns else []) + ["total_risk"]
                tbl = tbl[show_cols].rename(columns={"state": "State", "cases_recent": "Recent cases", "total_risk": "Final score"})
            else:
                tbl = sr[["state", "risk_tier", "risk_score"]].copy().rename(columns={"state": "State", "risk_tier": "Risk tier", "risk_score": "Risk score"})
            st.dataframe(tbl, use_container_width=True, hide_index=True)
            with st.expander("How state risk is calculated", expanded=False):
                has_ww_pts = "wastewater_points" in sr.columns and (sr["wastewater_points"].fillna(0) != 0).any()
                st.markdown(
                    "**State risk** combines: **Coverage risk** (0–50 pts) = max(0, 95 − coverage%) × 2; "
                    "**Case activity** (0–30 pts) = percentile of last 4-week cases vs other states; "
                    "**Wastewater activity** (0–20 pts) = percentile of last 4-week wastewater signal by state."
                )
                if not has_ww_pts:
                    st.caption("States without wastewater coverage get wastewater_points=0 and total score capped at 80 (coverage + cases only); they are not rescaled to 100.")
                st.markdown(
                    "**Risk tier:** **High** = total ≥ 70; **Medium** = 40–69; **Low** &lt; 40. "
                    "Thresholds and formulas are for situational awareness only."
                )
                br_cols = ["coverage_points", "case_points", "wastewater_points", "total_risk"]
                if all(c in sr.columns for c in br_cols):
                    ex = sr.iloc[0]
                    breakdown = pd.DataFrame([
                        ["Coverage", ex.get("coverage_points", 0)],
                        ["Cases", ex.get("case_points", 0)],
                        ["Wastewater", ex.get("wastewater_points", 0)],
                        ["Total", ex.get("total_risk", 0)],
                    ], columns=["Component", "Points"])
                    st.dataframe(breakdown, use_container_width=True, hide_index=True)
            st.subheader("AI report for a state")
            from dashboard.utils.state_maps import state_to_abbr, STATE_TO_ABBR
            abbr_to_name = {v: k for k, v in STATE_TO_ABBR.items()}
            seen_abbr = set()
            state_options = ["— Select a state —"]
            for _state in sorted(sr["state"].astype(str).unique()):
                abbr = state_to_abbr(_state)
                if abbr and abbr not in seen_abbr:
                    seen_abbr.add(abbr)
                    state_options.append(abbr_to_name.get(abbr, _state))
            selected = st.selectbox("Choose a state to generate a short AI summary", state_options, key="state_report_select")
            if selected and selected != "— Select a state —":
                selected_abbr = state_to_abbr(selected) or selected
                row = sr[sr["state"].astype(str).apply(lambda x: state_to_abbr(str(x)) == selected_abbr or str(x) == selected)].iloc[0]
                cov_pct = None
                kg = st.session_state.get("kg")
                if kg is not None and not kg.empty:
                    sc = next((c for c in ["state", "State", "jurisdiction", "geography"] if c in kg.columns), None)
                    pc = next((c for c in kg.columns if "pct" in c.lower() or "coverage" in c.lower()), None)
                    if sc and pc:
                        # Match by display name or abbreviation so we find the state either way
                        def _kg_state_match(val):
                            v = str(val).strip()
                            return v == selected or state_to_abbr(v) == selected_abbr
                        sub = kg[kg[sc].astype(str).apply(_kg_state_match)]
                        if not sub.empty:
                            cov_pct = pd.to_numeric(sub[pc], errors="coerce").mean()
                if st.button("Generate AI report for this state", key="btn_state_report"):
                    from dashboard.ollama_client import get_ollama_state_report
                    report = get_ollama_state_report(
                        selected, str(row["risk_tier"]), float(row["risk_score"]),
                        coverage_pct=cov_pct, data_as_of=st.session_state.get("data_as_of", ""),
                    )
                    if report:
                        st.markdown(report)
                    else:
                        st.warning("Could not generate report. Add **OLLAMA_API_KEY** to `.env` or check **dashboard.log**.")
        else:
            st.info("No state risk table yet. Ensure **Kindergarten** data loaded (see sidebar); then click **Refresh data**.")

    elif page == "Forecast":
        st.header("Forecast by state")
        st.caption("Outlook and main drivers by state. For situational awareness only.")
        sr = st.session_state.get("state_risk_df")
        if sr is not None and not sr.empty:
            def _outlook(tier):
                if tier == "high":
                    return "High"
                if tier == "medium":
                    return "Watch"
                return "Low"
            def _drivers(row):
                parts = []
                if "coverage_points" in row and row.get("coverage_points", 0) > 10:
                    parts.append("low coverage")
                if "case_points" in row and row.get("case_points", 0) > 10:
                    parts.append("recent cases")
                if "wastewater_points" in row and row.get("wastewater_points", 0) > 5:
                    parts.append("wastewater signal")
                if not parts:
                    return "Coverage and case levels in normal range."
                return "Mainly: " + ", ".join(parts) + "."
            forecast_table = sr.copy()
            forecast_table["Outlook"] = forecast_table["risk_tier"].apply(_outlook)
            forecast_table["What's driving it"] = forecast_table.apply(_drivers, axis=1)
            st.dataframe(forecast_table[["state", "Outlook", "What's driving it"]].rename(columns={"state": "State"}), use_container_width=True, hide_index=True)
            national_line = ""
            if st.session_state.get("forecast_df") is not None and not st.session_state.forecast_df.empty:
                fc = st.session_state.forecast_df
                mean_fc = float(fc["forecast"].mean())
                national_line = "Expected national cases in next 4 weeks: about %.0f (range %.0f–%.0f per week)." % (mean_fc * 4, fc["forecast"].min(), fc["forecast"].max())
                st.caption("**" + national_line + "**")
            st.subheader("AI interpretation")
            st.caption("States in summary: **%s** (validated US states)." % len(forecast_table))
            if st.session_state.get("forecast_ai_summary"):
                st.markdown(st.session_state.forecast_ai_summary)
                if st.button("Regenerate AI interpretation", key="forecast_ai_regen"):
                    st.session_state.forecast_ai_summary = None
                    st.rerun()
            else:
                if st.button("Generate AI interpretation", key="forecast_ai_btn"):
                    from dashboard.ollama_client import get_ollama_forecast_interpretation
                    outlook_counts = forecast_table["Outlook"].value_counts()
                    summary = "State outlooks: " + "; ".join([f"{k}: {v} states" for k, v in outlook_counts.items()]) + ". Sample drivers: " + "; ".join(forecast_table["What's driving it"].head(5).tolist())
                    # Current hotspots: top 5–10 states by risk_score
                    rank_col = "risk_score" if "risk_score" in forecast_table.columns else "total_risk"
                    if rank_col not in forecast_table.columns:
                        rank_col = None
                    if rank_col:
                        top_states = forecast_table.nlargest(10, rank_col)
                        hotspots_list = [f"{row['state']}: {float(row[rank_col]):.0f}" for _, row in top_states.iterrows()]
                        summary += " Current hotspots (top states by risk score): " + "; ".join(hotspots_list) + "."
                    report = get_ollama_forecast_interpretation(summary, national_line, st.session_state.get("data_as_of", ""))
                    st.session_state.forecast_ai_summary = report or "Could not generate (add OLLAMA_API_KEY to .env or check dashboard.log)."
                    st.rerun()
                else:
                    st.caption("Click **Generate AI interpretation** for a plain-language summary of the forecast. Requires **OLLAMA_API_KEY** in `.env`.")
        else:
            st.info("No state risk data yet. Load **Kindergarten** and click **Refresh data**.")

    if st.session_state.get("show_debug"):
        with st.expander("Debug", expanded=True):
            # NNDSS
            na = st.session_state.get("nndss_agg")
            au = st.session_state.get("nndss_audit", {})
            st.write("**NNDSS** — case_column_used:", au.get("case_column_used"), "| year_min:", au.get("year_min"), "| year_max:", au.get("year_max"))
            if na is not None and isinstance(na, pd.DataFrame) and not na.empty:
                st.write("Recent 5 (year, week, cases):")
                st.dataframe(na[["year", "week", "cases"]].tail(5), hide_index=True)
            else:
                st.write("(no NNDSS national weekly data)")
            # Wastewater
            ww_df = st.session_state.get("ww")
            if ww_df is not None and not ww_df.empty:
                from dashboard.risk import compute_ww_detection_frequency
                ww_weekly, ww_val = compute_ww_detection_frequency(ww_df, year_min=None, year_max=None)
                st.write("**Wastewater** — pcr_target_used:", ww_val.get("pcr_target_used"), "| weeks_min:", ww_val.get("weeks_min"), "| weeks_max:", ww_val.get("weeks_max"))
                if not ww_weekly.empty:
                    st.write("Recent 5 (year, week, detection_frequency):")
                    st.dataframe(ww_weekly[["year", "week", "detection_frequency"]].tail(5), hide_index=True)
                else:
                    st.write("(no weekly detection_frequency)")
            else:
                st.write("**Wastewater** — (no data)")
            # KG
            kg_df = st.session_state.get("kg")
            if kg_df is not None and not kg_df.empty:
                yc = next((c for c in ["school_year", "reporting_year", "year", "coverage_school_year"] if c in kg_df.columns), None)
                if not yc:
                    yc = next((c for c in kg_df.columns if "year" in c.lower()), None)
                if yc:
                    raw = kg_df[yc].astype(str).str.strip()
                    yr = pd.to_numeric(raw, errors="coerce")
                    valid = yr.notna() & (yr >= 2000) & (yr < 2100)
                    years = sorted(yr[valid].astype(int).unique().tolist())
                    st.write("**KG** — available years:", years)
                    for y in years:
                        n = (yr == y).sum()
                        st.write("  %s: %s rows" % (y, int(n)))
                else:
                    st.write("**KG** — no year column; columns:", list(kg_df.columns)[:10])
            else:
                st.write("**KG** — (no data)")


# Sidebar
with st.sidebar:
    st.title("Risk of Measles Outbreak in US")
    page = st.radio(
        "Page",
        ["Overview", "Historical trends", "Kindergarten coverage", "Wastewater vs NNDSS", "State risk", "Forecast"],
        label_visibility="collapsed",
    )
    show_debug = st.checkbox("Show debug panel", value=False, key="show_debug")
    refresh = st.button("Refresh data")
    use_cache = not refresh
    st.caption("Data sources")
    st.session_state.data_loaded = False
    try:
        load_and_model(use_cache=use_cache, outbreak_threshold=0)
        st.session_state.data_loaded = True
    except Exception as e:
        logger.exception("load_and_model failed")
        st.error("Load failed. Check logs.")
    for source, status in st.session_state.get("load_status", {}).items():
        label = "temporarily unavailable" if status == "fail" else status
        st.caption(f"  {source}: {label}")
    st.caption(f"Data as of: {st.session_state.get('data_as_of', 'N/A')}")
    st.caption("NNDSS range: we request all rows from CDC; the date range you see is what the agency has published.")

# Main content (app-level exception handler: log traceback, show generic message)
try:
    _render_main(page)
except Exception:
    logger.exception("Unhandled exception in main content")
    st.error("Something went wrong. Check the log file (e.g. dashboard/dashboard.log) for details.")
    st.stop()
