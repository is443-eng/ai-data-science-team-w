#!/usr/bin/env bash
# Single-command run for the Predictive Measles Risk Dashboard.
# From project root: ./run.sh (or: bash run.sh)

set -e
cd "$(dirname "$0")"

# Optional: activate venv if present
if [ -d "venv" ]; then
    source venv/bin/activate
elif [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# .env is loaded by the app from project root
export PYTHONPATH="$PWD"
exec streamlit run dashboard/app.py
