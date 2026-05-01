#!/usr/bin/env python3
"""
Run the App V3 Streamlit app locally for manual testing.

Usage (from ``Tool V3/``)::

    python run_me.py

From repo root::

    python "Tool V3/run_me.py"

Options::

    python run_me.py --port 8512
    python run_me.py --headless
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


def main() -> int:
    app_dir = Path(__file__).resolve().parent
    os.chdir(app_dir)
    if str(app_dir) not in sys.path:
        sys.path.insert(0, str(app_dir))

    p = argparse.ArgumentParser(description="Launch Tool V3 Streamlit app (local testing).")
    p.add_argument("--port", type=int, default=8501, help="Port for Streamlit (default: 8501)")
    p.add_argument(
        "--headless",
        action="store_true",
        help="Run without opening a browser (useful for CI or remote shells)",
    )
    args = p.parse_args()

    cmd: list[str] = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        str(app_dir / "app.py"),
        "--server.port",
        str(args.port),
        "--browser.gatherUsageStats",
        "false",
    ]
    if args.headless:
        cmd.extend(["--server.headless", "true"])

    print(f"Starting Streamlit from {app_dir}")
    print(f"URL: http://127.0.0.1:{args.port}/")
    print("Stop with Ctrl+C.\n")
    return subprocess.call(cmd)


if __name__ == "__main__":
    raise SystemExit(main())
