"""
Shiny for Python — measles surveillance dashboard.

- Data: dashboard.loaders.load_all() (CDC Socrata + historical CSV).
- Model: build_dashboard_payload from TestDashboard pipeline module.

Default pipeline path (your copy):
  TestDashboard/__pycache__/measles_risk_shiny_fast_pipeline (1).py
If missing, falls back to: TestDashboard/measles_risk_shiny_fast_pipeline.py

Run from project root:
  PYTHONPATH=. python3 -m shiny run TestDashboard/shiny_app.py

.env: SOCRATA_APP_TOKEN (project root or dashboard/.env)
"""
from __future__ import annotations

import importlib.util
import sys
import traceback
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import pandas as pd
from shiny import App, reactive, render, ui

_TEST = Path(__file__).resolve().parent
_PIPELINE_CANDIDATES = [
    _TEST / "__pycache__" / "measles_risk_shiny_fast_pipeline (1).py",
    _TEST / "measles_risk_shiny_fast_pipeline.py",
]
_PIPELINE_PATH = next((p for p in _PIPELINE_CANDIDATES if p.is_file()), None)
if _PIPELINE_PATH is None:
    raise FileNotFoundError(
        "Pipeline not found. Expected one of:\n  "
        + "\n  ".join(str(p) for p in _PIPELINE_CANDIDATES)
    )

_MOD_NAME = "measles_risk_shiny_fast_pipeline"
_spec = importlib.util.spec_from_file_location(_MOD_NAME, _PIPELINE_PATH)
_fp = importlib.util.module_from_spec(_spec)
assert _spec.loader is not None
sys.modules[_MOD_NAME] = _fp
_spec.loader.exec_module(_fp)

build_dashboard_payload = _fp.build_dashboard_payload
payload_to_value_boxes = _fp.payload_to_value_boxes
DEFAULT_ALERT_THRESHOLD = _fp.DEFAULT_ALERT_THRESHOLD
get_national_weekly_cases = _fp.get_national_weekly_cases
compute_ww_detection_frequency = _fp.compute_ww_detection_frequency

# ---------------------------------------------------------------------------
app_ui = ui.page_sidebar(
    ui.sidebar(
        ui.h4("Data"),
        ui.p(ui.tags.small(f"Pipeline: `{_PIPELINE_PATH.name}`")),
        ui.input_action_button("refresh", "Refresh (clear cache)", class_="btn-primary"),
        ui.input_slider(
            "outbreak_threshold",
            "Alert threshold (cases in next 4 weeks)",
            min=0,
            max=20,
            value=int(DEFAULT_ALERT_THRESHOLD),
            step=1,
        ),
        ui.h5("Sources"),
        ui.output_text_verbatim("sidebar_status"),
        ui.p(ui.tags.small("SOCRATA_APP_TOKEN in .env")),
    ),
    ui.h2("Measles surveillance dashboard"),
    ui.p(
        ui.tags.em("Situational awareness only · CDC data · Not clinical advice"),
        class_="text-muted",
    ),
    ui.navset_tab(
        ui.nav_panel(
            "Overview",
            ui.layout_columns(
                ui.card(ui.h5("Alarm (%)"), ui.output_ui("c_alarm")),
                ui.card(ui.h5("Signal / confidence"), ui.output_ui("c_signal")),
                ui.card(ui.h5("Latest week"), ui.output_ui("c_week")),
                col_widths=(4, 4, 4),
            ),
            ui.layout_columns(
                ui.card(ui.h5("Next 4w projection sum"), ui.output_ui("c_next4")),
                ui.card(ui.h5("Model"), ui.output_ui("c_model")),
                ui.card(ui.h5("Label"), ui.output_ui("c_label")),
                col_widths=(4, 4, 4),
            ),
        ),
        ui.nav_panel("Baseline projection", ui.output_data_frame("t_forecast")),
        ui.nav_panel("State composite index", ui.output_data_frame("t_states")),
        ui.nav_panel(
            "National NNDSS",
            ui.output_ui("p_nndss"),
            ui.output_data_frame("t_nndss"),
        ),
        ui.nav_panel(
            "Wastewater vs NNDSS",
            ui.output_ui("p_ww"),
        ),
        ui.nav_panel(
            "Diagnostics",
            ui.h4("Notes"),
            ui.output_text_verbatim("d_notes"),
            ui.h4("NNDSS"),
            ui.output_text_verbatim("d_nndss"),
            ui.h4("Modeling"),
            ui.output_text_verbatim("d_mod"),
            ui.h4("Wastewater state mapping"),
            ui.output_text_verbatim("d_ww_state"),
            ui.h4("Projection"),
            ui.output_text_verbatim("d_proj"),
            ui.h4("Errors"),
            ui.output_text_verbatim("d_err"),
        ),
    ),
    title="Measles dashboard",
)


def server(input, output, session):
    @reactive.calc
    def bundle():
        _ = input.refresh()
        thr = int(input.outbreak_threshold())
        out = {
            "load_status": {},
            "data_as_of": "",
            "payload": None,
            "nndss": pd.DataFrame(),
            "ww": pd.DataFrame(),
            "errors": [],
        }
        try:
            from dashboard.loaders import clear_cache, load_all
        except ImportError as e:
            out["errors"].append(str(e))
            return out
        try:
            if int(input.refresh()) > 0:
                clear_cache()
        except Exception:
            pass
        try:
            hist, kg, ww, nndss, load_status, data_as_of = load_all(use_cache=True)
            out["load_status"] = load_status
            out["data_as_of"] = data_as_of
            hist = hist if hist is not None else pd.DataFrame()
            kg = kg if kg is not None else pd.DataFrame()
            ww = ww if ww is not None else pd.DataFrame()
            nndss = nndss if nndss is not None else pd.DataFrame()
            out["nndss"] = nndss
            out["ww"] = ww
            out["payload"] = build_dashboard_payload(
                historical=hist,
                nndss=nndss,
                wastewater=ww,
                kindergarten=kg,
                outbreak_threshold=thr,
                include_debug_tables=False,
            )
        except Exception as e:
            out["errors"].append(f"{e}\n{traceback.format_exc()}")
        return out

    def P():
        p = bundle().get("payload")
        return p if p is not None else None

    @output
    @render.text
    def sidebar_status():
        b = bundle()
        lines = [f"As of: {b.get('data_as_of', '—')}"]
        for k, v in (b.get("load_status") or {}).items():
            lines.append(f"  {k}: {v}")
        return "\n".join(lines)

    @output
    @render.ui
    def c_alarm():
        p = P()
        if not p:
            return ui.p("—")
        bx = payload_to_value_boxes(p)
        return ui.p(f"{bx.get('alarm_probability_pct', '—')}%")

    @output
    @render.ui
    def c_signal():
        p = P()
        if not p:
            return ui.p("—")
        bx = payload_to_value_boxes(p)
        return ui.p(f"{bx.get('signal_level')} · conf {bx.get('confidence')}")

    @output
    @render.ui
    def c_week():
        p = P()
        if not p:
            return ui.p("—")
        nr = p.get("national_risk") or {}
        wk = nr.get("latest_week")
        s = f"{wk['year']}-W{wk['week']}" if isinstance(wk, dict) else "—"
        return ui.p(f"{s} · {nr.get('latest_cases', '—')} cases")

    @output
    @render.ui
    def c_next4():
        p = P()
        if not p:
            return ui.p("—")
        bx = payload_to_value_boxes(p)
        v = bx.get("next4w_baseline_cases")
        return ui.p("—" if v is None else str(v))

    @output
    @render.ui
    def c_model():
        p = P()
        if not p:
            return ui.p("—")
        nr = p.get("national_risk") or {}
        return ui.p(
            f"AUC {nr.get('auc')} · Brier {nr.get('brier')} · {nr.get('model_status')} · "
            f"{nr.get('n_train')}/{nr.get('n_test')}"
        )

    @output
    @render.ui
    def c_label():
        p = P()
        if not p:
            return ui.p("—")
        return ui.p((p.get("national_risk") or {}).get("label", "—"))

    @output
    @render.data_frame
    def t_forecast():
        p = P()
        if not p:
            return pd.DataFrame({"msg": ["No data"]})
        fc = p.get("forecast")
        if fc is None or fc.empty:
            return pd.DataFrame({"msg": ["No projection"]})
        return fc

    @output
    @render.data_frame
    def t_states():
        p = P()
        if not p:
            return pd.DataFrame({"msg": ["No data"]})
        sr = p.get("state_risk")
        if sr is None or sr.empty:
            return pd.DataFrame({"msg": ["No state rows"]})
        return sr

    @output
    @render.ui
    def p_nndss():
        b = bundle()
        n = b.get("nndss")
        if n is None or n.empty:
            return ui.p("No NNDSS.")
        agg, _ = get_national_weekly_cases(n)
        if agg.empty:
            return ui.p("Cannot aggregate national weekly.")
        import plotly.graph_objects as go

        d = agg.tail(104).copy()
        d["yw"] = d["year"].astype(int).astype(str) + "-W" + d["week"].astype(int).astype(str)
        fig = go.Figure(go.Scatter(x=d["yw"], y=d["cases"], mode="lines+markers"))
        fig.update_layout(title="National weekly cases (last 104)", height=400, xaxis_tickangle=-45)
        return ui.HTML(fig.to_html(include_plotlyjs="cdn", full_html=False))

    @output
    @render.data_frame
    def t_nndss():
        b = bundle()
        n = b.get("nndss")
        if n is None or n.empty:
            return pd.DataFrame()
        agg, _ = get_national_weekly_cases(n)
        return agg.tail(15)[["year", "week", "cases"]] if not agg.empty else pd.DataFrame()

    @output
    @render.ui
    def p_ww():
        b = bundle()
        n, w = b.get("nndss"), b.get("ww")
        if n is None or n.empty or w is None or w.empty:
            return ui.p("Need NNDSS and wastewater.")
        ww_w, _ = compute_ww_detection_frequency(w)
        agg, _ = get_national_weekly_cases(n)
        if ww_w.empty or agg.empty:
            return ui.p("Weekly series empty.")
        m = ww_w.copy()
        m["year"] = m["year"].astype(int)
        agg = agg.copy()
        agg["year"] = pd.to_numeric(agg["year"], errors="coerce").astype(int)
        j = m.merge(agg[["year", "week", "cases"]], on=["year", "week"], how="inner")
        if j.empty:
            return ui.p("No overlapping weeks.")
        import plotly.graph_objects as go

        j = j.sort_values(["year", "week"])
        j["yw"] = j["year"].astype(str) + "-W" + j["week"].astype(int).astype(str)
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=j["yw"], y=j["detection_frequency"], name="Det. freq", yaxis="y"))
        fig.add_trace(go.Scatter(x=j["yw"], y=j["cases"], name="Cases", yaxis="y2"))
        fig.update_layout(
            title="Wastewater detection frequency vs NNDSS",
            yaxis=dict(tickformat=".0%"),
            yaxis2=dict(overlaying="y", side="right", title="Cases"),
            height=420,
            xaxis_tickangle=-45,
        )
        return ui.HTML(fig.to_html(include_plotlyjs="cdn", full_html=False))

    @output
    @render.text
    def d_notes():
        p = P()
        if not p:
            return "—"
        n = (p.get("diagnostics") or {}).get("notes") or []
        return "\n".join(str(x) for x in n)

    @output
    @render.text
    def d_nndss():
        p = P()
        if not p:
            return "—"
        d = (p.get("diagnostics") or {}).get("nndss") or {}
        return "\n".join(f"{k}: {v}" for k, v in d.items()) or "—"

    @output
    @render.text
    def d_mod():
        p = P()
        if not p:
            return "—"
        d = (p.get("diagnostics") or {}).get("modeling") or {}
        return "\n".join(f"{k}: {v}" for k, v in d.items()) or "—"

    @output
    @render.text
    def d_ww_state():
        p = P()
        if not p:
            return "—"
        d = (p.get("diagnostics") or {}).get("wastewater_state") or {}
        if not d:
            return "—"
        return "\n".join(f"{k}: {v}" for k, v in d.items()) or "—"

    @output
    @render.text
    def d_proj():
        p = P()
        if not p:
            return "—"
        d = (p.get("diagnostics") or {}).get("projection") or {}
        return "\n".join(f"{k}: {v}" for k, v in d.items()) or "—"

    @output
    @render.text
    def d_err():
        e = bundle().get("errors") or []
        return "\n".join(e) if e else "(none)"


app = App(app_ui, server)
