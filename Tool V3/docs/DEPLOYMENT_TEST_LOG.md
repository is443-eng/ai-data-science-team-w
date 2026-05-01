# Deployment test log (Tool V2)

Use this log while following **Deploy testing first, documentation package last**. Update checkboxes as you complete each step.

## 1. Dry-run (no Connect credentials required)

From the `Tool V2/` directory:

```bash
python3 deployment/deploy_me.py --dry-run
```

- [x] **Verified:** Command prints a single `rsconnect.main deploy streamlit` line, working directory is `Tool V2`, exit code `0`.  
- **Last run (automated):** dry-run succeeds; `CONNECT_API_KEY` may show `<missing>` until `.env` contains a key (expected for dry-run).

## 2. Real deploy (requires API key)

1. Install deploy deps: `pip install -r deployment/requirements-deploy.txt`
2. Set one of: `CONNECT_API_KEY`, `POSIT_PUBLISHER_KEY`, `POSIT_CONNECT_PUBLISHER`, or `RSCONNECT_API_KEY` in repo or `Tool V2` `.env`.
3. Optional: set `SOCRATA_APP_TOKEN`, `OPENAI_API_KEY` (recommended for agent tool calling), and/or `OLLAMA_API_KEY` so the script forwards them (`-E`) to Connect.
4. Run:

```bash
cd "Tool V2"
python3 deployment/deploy_me.py
```

Or update existing content: `python3 deployment/deploy_me.py --app-id <guid>`

- [ ] **Completed:** Deploy finished with exit code `0`.
- [ ] **Live URL recorded** in [`submission_notes.md`](submission_notes.md) (copy from Connect UI or rsconnect output).

## 3. Smoke test (browser)

After you have a **live URL**, run through the checklist in [`submission_notes.md`](submission_notes.md) and [`MANUAL_QA_CHECKLIST.md`](MANUAL_QA_CHECKLIST.md).

Optional quick HTTP check (replace the URL):

```bash
bash deployment/smoke_check_url.sh 'https://connect.example.com/your-content/'
```

- [ ] App loads (HTTP 200; Streamlit shell visible).
- [ ] Sidebar **Refresh data** does not hard-crash.
- [ ] **Overview** + at least one other tab spot-checked.

## Notes

- A **dry-run** does not replace a real deploy or browser verification.
- If deploy fails, see [`deployment/README.md`](../deployment/README.md) and `python3 deployment/deploy_me.py --help`.
