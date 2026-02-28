# CDC Measles Data — Dataset Overview

This document summarizes the five CDC data sources used in this project. Each dataset is accessed via the CDC Socrata API on data.cdc.gov. All API scripts apply data cleaning so that only measles-related (or MMR vaccination) data is returned. Child and teen vaccination scripts further restrict to national and state-level geography only (HHS regions are excluded).

---

## 1. NNDSS — National Notifiable Diseases Surveillance System

**View ID:** `x9gk-5huc` | **Script:** `call_cdc_nndss.py`

### Summary

NNDSS provides measles case counts (indigenous and imported) at weekly intervals. Data is reported in MMWR weeks (1–52) and covers multiple years. Records are divided at the national level (US RESIDENTS) and by state (Location1 populated). The cleaned dataset includes only "Measles, Indigenous" and "Measles, Imported" labels.

### Column Overview

| Column | Description / Range |
|--------|---------------------|
| states | Reporting Area; "US RESIDENTS" for national, or state/territory name |
| year | MMWR year (e.g., 2019–2024) |
| week | MMWR week number (1–52) |
| label | "Measles, Indigenous" or "Measles, Imported" |
| location1 | State name when row is state-level; empty for national |
| m1 | Current week case count |
| m2 | Previous 52-week max |
| m3 | Cumulative YTD current year |
| m4 | Cumulative YTD previous year |
| m1_flag, m2_flag, m3_flag, m4_flag | Data quality flags (e.g., "-" for suppressed) |
| location2, sort_order, geocode | Geographic and sort metadata |

---

## 2. Child Vaccination — Young Children (0–35 Months)

**View ID:** `fhky-rtsk` | **Script:** `call_cdc_child_vax.py`

### Summary

Child vaccination coverage estimates for MMR (≥1 Dose MMR) among children 0–35 months. **Cleaning keeps only national and state-level data:** United States (national) and all States/Local Areas; HHS regions are excluded. Estimates are by birth year or birth-year cohort and can be broken down by age and sociodemographic dimensions (race/ethnicity, poverty, insurance, urbanicity).

### Column Overview

| Column | Description / Range |
|--------|---------------------|
| vaccine | Vaccine name; cleaned to "≥1 Dose MMR" only |
| dose | Dose level (e.g., ≥1, ≥2); may be empty for this vaccine |
| geography_type | After cleaning: "States/Local Areas" only (or national row has geography = United States) |
| geography | United States (national) or state/local area names; HHS regions excluded |
| year_season | Birth year or birth-year cohort (e.g., 2011, 2016–2017) |
| dimension_type | Age, Race and Ethnicity, Poverty, Insurance Coverage, Urbanicity, Overall |
| dimension | Specific group (e.g., "19 Months", "Hispanic") |
| coverage_estimate | Estimated vaccination rate (percent) |
| _95_ci | 95% confidence interval |
| population_sample_size | Survey sample size |

---

## 3. Teen Vaccination — Adolescents (13–17 Years)

**View ID:** `ee48-w5t6` | **Script:** `call_cdc_teen_vax.py`

### Summary

Adolescent MMR vaccination coverage (≥2 Doses MMR) from the National Immunization Survey-Teen. **Cleaning keeps only national and state-level data:** United States (national) and all States/Local Areas; HHS regions are excluded. Survey years span 2006–2024. Estimates can be broken down by age (13–17, 13–15) and sociodemographic dimensions.

### Column Overview

| Column | Description / Range |
|--------|---------------------|
| vaccine | Vaccine name; cleaned to "≥2 Doses MMR" only |
| dose | Dose description; may be empty |
| geography_type | After cleaning: "States/Local Areas" only (or national row has geography = United States) |
| geography | United States (national) or state/local area names; HHS regions excluded |
| year_season | Survey year (2006–2024) |
| dimension_type | Age, Race and Ethnicity, Insurance, Urbanicity, Poverty, Overall |
| dimension | Age group (e.g., "13–17 Years") or sociodemographic group |
| coverage_estimate | Estimated vaccination rate (percent) |
| _95_ci | 95% confidence interval |
| population_sample_size | Survey sample size |

---

## 4. Kindergarten Vaccination and Exemptions

**View ID:** `ijqb-a7ye` | **Script:** `call_cdc_kindergarten_vax.py`

### Summary

MMR vaccination coverage and exemption data among kindergartners from the School Vaccination Assessment Program. Data is at national and state levels. School years span 2009–10 through 2024–25. Cleaned dataset includes "MMR" and "MMR (PAC)" vaccine types.

### Column Overview

| Column | Description / Range |
|--------|---------------------|
| vaccine | Vaccine type; cleaned to "MMR" or "MMR (PAC)" |
| dose | Dose/UTD description (e.g., "2 Doses (unknown disease history)") |
| geography_type | "National" or "States" |
| geography | U.S. Median, state names |
| year_season | School year (e.g., "2023-24", "2024-25") |
| coverage_estimate | Vaccination or exemption rate (percent); may be "NA" or "NReq" |
| population_sample_size | Kindergarten enrollment count |
| percent_surveyed | Percent of kindergartners surveyed |
| foot_notes | Data quality symbols |
| survey_type | Census, stratified sample, voluntary response, etc. |

---

## 5. CDC Wastewater — Measles

**View ID:** `akvg-8vrb` | **Script:** `call_cdc_wastewater.py`

### Summary

Measles wastewater PCR data from CDC's National Wastewater Surveillance System (NWSS). Data includes sewershed-level measurements and flow-population-normalized concentration metrics. Sources include state/territory health departments, CDC's national testing contract (cdc_verily), and WastewaterSCAN (wws).

### Column Overview

| Column | Description / Range |
|--------|---------------------|
| record_id | Unique row identifier |
| sewershed_id | Anonymous identifier for wastewater treatment plant |
| wwtp_jurisdiction | State/territory (2-letter code, e.g., ca, tx) |
| source | state_territory, cdc_verily, or wws |
| county_fips | County FIPS code |
| counties_served | Counties served by sewershed |
| population_served | Population served |
| sample_id | Sample identifier |
| sample_collect_date | Date of sample collection |
| sample_type | Sample type |
| sample_matrix | Sample matrix (e.g., wastewater) |
| sample_location | Sampling location |
| pcr_target | PCR target; cleaned to measles only (MeV_WT, case-insensitive) |
| pcr_gene_target_agg | Gene-level assay target |
| pcr_target_avg_conc | Average PCR concentration |
| pcr_target_units | Concentration units |
| pcr_target_flowpop_lin | Flow-population-normalized concentration |
| pcr_target_mic_lin | Microbial-normalized concentration |
| hum_frac_target_mic | Human fraction target |
| rec_eff_percent | Recovery efficiency |
| date_updated | Last update timestamp |

---

## API Usage

All scripts require `SOCRATA_APP_TOKEN` in `.env`. Run from the **Shiny App V1** folder (or with that folder on the path):

```bash
cd "Shiny App V1"
python call_cdc_nndss.py
python call_cdc_child_vax.py
python call_cdc_teen_vax.py
python call_cdc_kindergarten_vax.py
python call_cdc_wastewater.py
```

- **Row limit:** Default is 50,000 rows per request (Socrata maximum). Use `--limit N` to override.
- **Other options:** `--schema` to list columns, `--out <file>` to save CSV, `--where ""` to disable the default filter.

## Verification

Run `python test_cdc_api_cleaning.py` to verify that all five scripts return cleaned data and pass assertion checks.
