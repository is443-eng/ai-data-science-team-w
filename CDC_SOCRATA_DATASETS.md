# CDC Socrata datasets — same app token

Use the same **`SOCRATA_APP_TOKEN`** (in `.env`) for all of these. They are all on `data.cdc.gov`.

| Dataset | View ID | Description |
|--------|---------|-------------|
| NNDSS Weekly Reports | `x9gk-5huc` | Measles cases (domestic/imported); use `call_cdc_api.py` |
| CDC Wastewater – Measles | `akvg-8vrb` | Wastewater data for measles |
| Teen Vaccination Coverage (13–17) | `ee48-w5t6` | Vaccination coverage, adolescents |
| Child Vaccination Coverage (0–35 mo) | `fhky-rtsk` | Vaccination coverage, young children |
| Kindergarten Vaccination & Exemptions | `ijqb-a7ye` | Kindergarten vaccination coverage and exemptions |

## API pattern (legacy GET)

Same as `call_cdc_api.py`, but change the view ID:

```
GET https://data.cdc.gov/resource/{VIEW_ID}.json?$select=*&$limit=1000
Header: X-App-Token: <SOCRATA_APP_TOKEN>
```

Optional: `$where=...` for filters (SoQL).

## API pattern (SODA3 POST)

```
POST https://data.cdc.gov/api/v3/views/{VIEW_ID}/query.json
Headers: X-App-Token, Content-Type: application/json
Body: {"query": "SELECT *", "page": {"pageNumber": 1, "pageSize": 1000}}
```

Replace `{VIEW_ID}` with any of the IDs in the table (e.g. `akvg-8vrb`, `ee48-w5t6`, `fhky-rtsk`, `ijqb-a7ye`).

## Quick cURL (any dataset)

```bash
# Set once
export SOCRATA_APP_TOKEN="your_token_from_env"

# Example: wastewater (akvg-8vrb), first 100 rows
curl -H "X-App-Token: $SOCRATA_APP_TOKEN" \
  "https://data.cdc.gov/resource/akvg-8vrb.json?\$select=*&\$limit=100"
```

To inspect columns for a dataset, use the metadata URL (no token required):

- `https://data.cdc.gov/api/views/akvg-8vrb.json`
- `https://data.cdc.gov/api/views/ee48-w5t6.json`
- etc.

---

**Note:** `data.wastewaterscan.org` in `api_info.md` is a different source (not this Socrata API). The CDC wastewater dataset above is `akvg-8vrb` on `data.cdc.gov`.
