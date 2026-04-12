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

3. **`.env`** — If `python-dotenv` is installed (already in the main app `requirements.txt`), the script loads **repo root** `.env` and **`Tool V2/.env`** before reading variables (same pattern as other deploy scripts that centralize config).

4. **Server URL** — Default is the Cornell Connect URL above. Override with `CONNECT_SERVER` or `POSIT_CONNECT_SERVER`, or `--server`.

5. **App directory** — `deploy_me.py` deploys the **Tool V2** folder, using `app.py` as the Streamlit entrypoint and `requirements.txt` for the bundle. Default **Python 3.12** (`--override-python-version`); override with `--python-version 3.11` if needed.

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

The app needs **`SOCRATA_APP_TOKEN`** (CDC data) and optionally **`OLLAMA_API_KEY`** (AI features).

**Automatic forwarding:** If those variables are set in the environment when you run `deploy_me.py` (including after loading `.env`), the script adds `rsconnect` **`-E SOCRATA_APP_TOKEN`** and **`-E OLLAMA_API_KEY`** so their current values are stored on the Connect content. Values are **not** echoed in the printed command for name-only `-E` flags (only the variable name appears).

Use **`--no-app-env`** if you prefer to set vars only in the Connect UI and not copy them from your laptop.

You can still add more with **`-E NAME[=VALUE]`** (repeatable). Manual **`-E`** entries take precedence; auto-forward skips a name if you already passed it.

If you deploy without these in `.env`, add them later under Connect → content → **Vars**.

## Usage

Preview the command without contacting the server:

```bash
cd "Tool V2"
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

## References

- [rsconnect-python](https://docs.posit.co/rsconnect-python/)
- [Publishing from the command line](https://docs.posit.co/connect/user/publishing-cli/)
