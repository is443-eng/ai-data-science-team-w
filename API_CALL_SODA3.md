# CDC Socrata API — SODA3 Access

This document describes how to access CDC data on the Socrata (Tyler Data & Insights) platform using the **SODA3 API**. SODA3 requires identifying the caller (app token or other credentials) and supports a v3 query endpoint.

The script **`call_cdc_api.py`** uses dataset **x9gk-5huc** and supports both legacy GET and SODA3 POST (via `--soda3`). By default it fetches rows where the `label` column matches “Measles” (all columns); use `--where ""` for no filter.

**References:**
- [SODA3 API – Data & Insights](https://support.socrata.com/hc/en-us/articles/34730618169623-SODA3-API) — authentication, behavior, and what’s new.
- [Socrata Developer Portal – API Endpoints](https://dev.socrata.com/docs/endpoints) — v3 endpoint format and versioning.
- [CDC dataset (foundry) x9gk-5huc](https://dev.socrata.com/foundry/data.cdc.gov/x9gk-5huc) — dataset used by `call_cdc_api.py`.

---

## 1. Base URL and dataset

- **Domain:** `https://data.cdc.gov`
- **Dataset used in `call_cdc_api.py`:** identifier `x9gk-5huc`  
  - Legacy resource URL: `https://data.cdc.gov/resource/x9gk-5huc.json`  
  - SODA3 query endpoint: `https://data.cdc.gov/api/v3/views/x9gk-5huc/query.json`  
  - View metadata (for `--schema`): `https://data.cdc.gov/api/views/x9gk-5huc.json`

Other CDC datasets use the same pattern; replace the identifier in the paths above.

---

## 2. Authentication (required for SODA3)

SODA3 requests must identify the caller. For public CDC datasets, use an **app token**.

- **Header name:** `X-App-Token`
- **Header value:** your app token string (from [data.cdc.gov profile → Developer Settings](https://data.cdc.gov/profile/edit/developer_settings)).

Example (generic):

```http
X-App-Token: YOUR_APP_TOKEN
```

Store the token in `.env` as `SOCRATA_APP_TOKEN` and never commit it.

---

## 3. SODA3 query endpoint (POST + SoQL)

SODA3 uses a **POST** request to the **query** endpoint with a JSON body that includes the SoQL query and options.

**Endpoint:**

```text
POST https://data.cdc.gov/api/v3/views/x9gk-5huc/query.json
```

**Headers:**

| Header          | Value              |
|-----------------|--------------------|
| `X-App-Token`   | Your app token     |
| `Content-Type`  | `application/json` |

**Body (example — default in `call_cdc_api.py`: Measles rows, all columns, limit 1000):**

```json
{
  "query": "SELECT * WHERE lower(label) like '%measles%'",
  "page": {
    "pageNumber": 1,
    "pageSize": 1000
  }
}
```

**SoQL used in `call_cdc_api.py`:**

- **SELECT:** `*` (all columns)
- **WHERE:** optional; default is `lower(label) like '%measles%'`. Omit WHERE (or use `--where ""`) for no filter.
- **Limit:** via `page.pageSize` (script default 1000; override with `--limit`).

**Response:** Either a JSON array of row objects, or an object with a `data` key containing the array. The script handles both.

---

## 4. Legacy SODA 2.1 style (GET, still supported)

`call_cdc_api.py` uses the **legacy** endpoint by default; pass `--soda3` to use the SODA3 POST endpoint instead.

**Endpoint:**

```text
GET https://data.cdc.gov/resource/x9gk-5huc.json
```

**Headers:**

```http
X-App-Token: YOUR_APP_TOKEN
```

**Query parameters (SoQL via `$` params):**

| Parameter | Value |
|-----------|--------|
| `$select` | `*` (all columns) |
| `$where`  | optional; default `lower(label) like '%measles%'` |
| `$limit`  | e.g. `1000` (script default) |

**Example (default Measles filter, limit 1000):**

```text
https://data.cdc.gov/resource/x9gk-5huc.json?$select=*&$where=lower(label)%20like%20%27%25measles%25%27&$limit=1000
```

(Use proper encoding for `$where` in your client.)

---

## 5. Minimal cURL examples

**SODA3 (POST) — default Measles filter, limit 1000:**

```bash
curl -X POST "https://data.cdc.gov/api/v3/views/x9gk-5huc/query.json" \
  -H "X-App-Token: YOUR_APP_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"query":"SELECT * WHERE lower(label) like '\''%measles%'\''","page":{"pageNumber":1,"pageSize":1000}}'
```

**Legacy (GET) — same default:**

```bash
curl -H "X-App-Token: YOUR_APP_TOKEN" \
  "https://data.cdc.gov/resource/x9gk-5huc.json?\$select=*&\$where=lower(label)%20like%20%27%25measles%25%27&\$limit=1000"
```

Replace `YOUR_APP_TOKEN` with your actual token (or set `SOCRATA_APP_TOKEN` in `.env`).

---

## 6. Summary

| Item        | SODA3 (v3) | Legacy (default in script) |
|------------|------------|----------------------------|
| URL        | `https://data.cdc.gov/api/v3/views/x9gk-5huc/query.json` | `https://data.cdc.gov/resource/x9gk-5huc.json` |
| Method     | POST       | GET                        |
| Auth       | `X-App-Token` header | `X-App-Token` header  |
| Query      | JSON body with `query` (SoQL) and `page` | `$select`, `$where`, `$limit` |

Both require an app token (`SOCRATA_APP_TOKEN` in `.env`). **`call_cdc_api.py`** uses legacy GET by default; use the `--soda3` flag to call the SODA3 POST endpoint. Other options: `--where` (SoQL WHERE; default Measles filter), `--limit` (default 1000), `--out` (save JSON), `--schema` (print column list from view metadata).
