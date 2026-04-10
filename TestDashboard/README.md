# TestDashboard — Shiny

## Run

From **project root**:

```bash
python3 -m pip install -r TestDashboard/requirements-shiny.txt
PYTHONPATH=. python3 -m shiny run TestDashboard/shiny_app.py
```

Use a venv if your system Python blocks `pip install` (PEP 668).

## Pipeline file

`shiny_app.py` loads the pipeline from, in order:

1. `TestDashboard/__pycache__/measles_risk_shiny_fast_pipeline (1).py`
2. `TestDashboard/measles_risk_shiny_fast_pipeline.py` (if you move/rename the module here)

## Data

`dashboard/loaders.py` → `load_all()` (same CDC APIs as the Streamlit app). Set `SOCRATA_APP_TOKEN` in `.env`.
