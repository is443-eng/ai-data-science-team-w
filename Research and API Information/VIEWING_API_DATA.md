# How to View API Data (Step by Step)

Example script: **call_cdc_child_vax.py** (Child vaccination coverage 0–35 months).

---

## Prerequisites

1. **Dependencies** (from project root):
   ```bash
   pip install -r requirements.txt
   ```
   Or at least: `pip install requests pandas python-dotenv`

2. **App token** in `.env`:
   ```bash
   SOCRATA_APP_TOKEN=your_token_here
   ```
   Get a token: [data.cdc.gov → Profile → Developer Settings](https://data.cdc.gov/profile/edit/developer_settings).

---

## Option A: See data in the terminal (table)

1. Open a terminal and go to the project folder:
   ```bash
   cd /Users/mjt/Desktop/ai-data-science-team-w
   ```

2. Run the script with `--table` so every row is printed. Use a small `--limit` first so the output is manageable:
   ```bash
   python3 call_cdc_child_vax.py --table --limit 20
   ```
   (Use `python` instead of `python3` if that’s what you have.)

3. You’ll see:
   - A line like `Records returned: 20`
   - A line listing column names
   - Then the full table: one row per line, columns aligned.

4. To see more rows, increase the limit or omit it (default 1000):
   ```bash
   python3 call_cdc_child_vax.py --table --limit 100
   ```

---

## Option B: See data in a spreadsheet (CSV)

1. Open a terminal and go to the project folder:
   ```bash
   cd /Users/mjt/Desktop/ai-data-science-team-w
   ```

2. Run the script with `--out` and a filename. Create a folder for data if you want:
   ```bash
   mkdir -p data/raw
   python3 call_cdc_child_vax.py --out data/raw/child_vax.csv
   ```

3. You’ll see something like:
   ```
   Records returned: 1000
   Columns: year, state, vaccine_name, ...
   Saved to data/raw/child_vax.csv (CSV)
   ```

4. Open the CSV in a spreadsheet:
   - **macOS:** `open data/raw/child_vax.csv` (opens in Numbers by default)
   - Or double‑click the file in Finder, or open it from Excel/Google Sheets.

5. In the spreadsheet you can scroll, sort, filter, and look at all columns side by side.

---

## Same idea for other scripts

| Script                 | Example command (table)              | Example command (CSV)                    |
|------------------------|--------------------------------------|------------------------------------------|
| call_cdc_child_vax.py  | `python3 call_cdc_child_vax.py --table --limit 20`  | `python3 call_cdc_child_vax.py --out data/raw/child_vax.csv`  |
| call_cdc_teen_vax.py   | `python3 call_cdc_teen_vax.py --table --limit 20`  | `python3 call_cdc_teen_vax.py --out data/raw/teen_vax.csv`    |
| call_cdc_wastewater.py | `python3 call_cdc_wastewater.py --table --limit 20`| `python3 call_cdc_wastewater.py --out data/raw/wastewater.csv`|
| call_cdc_api.py        | `python3 call_cdc_api.py --table --limit 20`       | `python3 call_cdc_api.py --out data/raw/measles.csv`          |

Replace `python3` with `python` or `venv/bin/python` if that’s what you use.

---

## See every value for one column (e.g. vaccine)

1. Get the exact column name (API column names may differ from labels, e.g. `vaccine_name` not `vaccine`):
   ```bash
   python call_cdc_child_vax.py --schema
   ```

2. Print all distinct values for that column in the terminal:
   ```bash
   python call_cdc_child_vax.py --unique vaccine_name
   ```
   Use the `fieldName` from `--schema` (e.g. `vaccine_name`, `state`, `year`).
