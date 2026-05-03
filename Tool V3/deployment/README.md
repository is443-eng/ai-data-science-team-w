# Posit Connect deployment

Target server: [Cornell Systems Engineering Connect](https://connect.systems-apps.com/) (`https://connect.systems-apps.com/`).

## Prerequisites

1. **API key** — Create a Posit Connect API key with permission to deploy. Set one of (first match wins):
   - `CONNECT_API_KEY` (preferred by `rsconnect`)
   - `POSIT_PUBLISHER_KEY`
   - `POSIT_CONNECT_PUBLISHER` (alias used by some projects)
   - `RSCONNECT_API_KEY`

   The script copies the chosen value into `CONNECT_API_KEY` for the subprocess (same idea as passing `-k` to `rsconnect`, without putting the key in argv).

2. **CLI** — Install the deploy tool (once per machine or venv):

   ```bash
   pip install -r deployment/requirements-deploy.txt
   ```

   `deploy_me.py` runs **`python -m rsconnect.main deploy streamlit …`** so publishing works even when the `rsconnect` executable is not on `PATH` (common on Windows).

3. **`.env`** — If `python-dotenv` is installed (already in the main app `requirements.txt`), the script loads **repo root** `.env` and **`Tool V3/.env`** before reading variables (same pattern as other deploy scripts that centralize config).

4. **Server URL** — Default is the Cornell Connect URL above. Override with `CONNECT_SERVER` or `POSIT_CONNECT_SERVER`, or `--server`.

5. **App directory** — `deploy_me.py` deploys the **Tool V3** folder, using `app.py` as the Streamlit entrypoint and `requirements.txt` for the bundle. Default **Python 3.12.4** (matches Cornell Connect’s local env); override with `--python-version X.Y.Z` if your server differs.

6. **Bundle size** — Default **exclude** patterns (`-x`) mirror common practice: `tests`, `.pytest_cache`, `__pycache__`, `deployment`, `scripts`, `docs`, `reference`, `baseline`. Add more with `python deployment/deploy_me.py -x mypattern`.

## Optional deploy environment variables

| Variable | Purpose |
|----------|---------|
| `DEPLOY_STREAMLIT_TITLE` | Stable title when you do not pass `--title` (otherwise a unique default title is generated). |
| `DEPLOY_CONNECT_APP_ID` | Existing Connect content GUID to update when you omit `--app-id`. |

## Extra rsconnect flags (wrapped by `deploy_me.py`)

| Flag | Maps to |
|------|---------|
| `-E` / `--env` `NAME[=VALUE]` | Forward runtime env to Connect (repeatable). |
| `--no-verify` | `rsconnect --no-verify` (skip post-deploy HTTP check). |

## Runtime environment on Posit Connect

Set **`SOCRATA_APP_TOKEN`** for reliable CDC pulls and for child/teen tools that query Socrata directly (optional but recommended—see [`../docs/TECHNICAL_DETAILS.md`](../docs/TECHNICAL_DETAILS.md)). For **Insights** and tab AI text, set **`OPENAI_API_KEY`** (preferred) and/or **`OLLAMA_API_KEY`** on Connect.

**Automatic forwarding:** If those variables are set in the environment when you run `deploy_me.py` (including after loading `.env`), the script adds `rsconnect` **`-E`** entries for **`SOCRATA_APP_TOKEN`**, **`OLLAMA_API_KEY`**, **`OPENAI_API_KEY`**, and **`OPENAI_MODEL`** (when set) so their values are stored on the Connect content. Values are **not** echoed in the printed command for name-only `-E` flags (only the variable name appears).

**LLM provider on Connect:** Set **`OPENAI_API_KEY`** (and optionally **`OPENAI_MODEL`**, e.g. `gpt-4o-mini`) to use OpenAI for all agent and tab AI text. If **`OPENAI_API_KEY`** is unset, the app uses **`OLLAMA_API_KEY`** (Ollama Cloud) as before.

Use **`--no-app-env`** if you prefer to set vars only in the Connect UI and not copy them from your laptop.

You can still add more with **`-E NAME[=VALUE]`** (repeatable). Manual **`-E`** entries take precedence; auto-forward skips a name if you already passed it.

If you deploy without these in `.env`, add them later under Connect → content → **Vars**.

## Usage

Preview the command without contacting the server:

```bash
cd "Tool V3"
python deployment/deploy_me.py --dry-run
```

Deploy (creates **new** content with a **unique title** by default):

```bash
python deployment/deploy_me.py
```

Update **existing** content instead of creating a new deployment:

```bash
python deployment/deploy_me.py --app-id <guid-from-connect>
```

See `python deployment/deploy_me.py --help` for all options.

## After deploy: testing and recording the URL

1. Track dry-run and real deploy in [`../docs/DEPLOYMENT_TEST_LOG.md`](../docs/DEPLOYMENT_TEST_LOG.md).
2. Copy the live content URL into [`../docs/submission_notes.md`](../docs/submission_notes.md).
3. Optional: `bash deployment/smoke_check_url.sh 'https://…'` then run the browser checklist in `submission_notes.md`.

## Current deployment (as shipped — Tool V3)

| | |
|--|--|
| **Content GUID** | `b8cfc1fa-8eb0-4c2e-ba98-b5f06837e933` |
| **Direct URL** | https://connect.systems-apps.com/content/b8cfc1fa-8eb0-4c2e-ba98-b5f06837e933/ |

Update command: `python deployment/deploy_me.py --app-id b8cfc1fa-8eb0-4c2e-ba98-b5f06837e933` (add `--no-verify` if the CLI post-check flakes while the app is healthy).

## References

- [rsconnect-python](https://docs.posit.co/rsconnect-python/)
- [Publishing from the command line](https://docs.posit.co/connect/user/publishing-cli/)
