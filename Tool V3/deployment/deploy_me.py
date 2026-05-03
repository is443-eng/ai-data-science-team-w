#!/usr/bin/env python3
"""
Deploy Tool V3 Streamlit app to Posit Connect using ``rsconnect-python``.

Default server: https://connect.systems-apps.com/

Authentication: set ``CONNECT_API_KEY``, ``POSIT_PUBLISHER_KEY``, or other supported
vars (see ``_resolve_api_key``) — or load them from the repo ``.env`` via
``python-dotenv``.

New deployments use a unique content title (UUID suffix) unless you pass ``--title``,
set ``DEPLOY_STREAMLIT_TITLE``, or ``--app-id`` / ``DEPLOY_CONNECT_APP_ID``.

The Connect bundle requests **Python 3.12.4** by default (``--override-python-version``); Cornell Connect currently exposes 3.12.4, not 3.12.0.

If ``SOCRATA_APP_TOKEN``, ``OLLAMA_API_KEY``, ``OPENAI_API_KEY``, and/or ``OPENAI_MODEL``
are set in the environment used to run this script (including after loading ``.env``),
they are forwarded to the published content via ``rsconnect -E`` so the live app can reach CDC and LLM APIs.

Invocation uses ``python -m rsconnect.main`` so deploy works when ``rsconnect`` is
not on ``PATH``.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
import uuid
from pathlib import Path


DEFAULT_SERVER = "https://connect.systems-apps.com/"
DEFAULT_PYTHON_VERSION = "3.12.4"

# Default bundle excludes (rsconnect ``-x``): shrink upload and skip non-runtime paths.
DEFAULT_EXCLUDES = (
    "tests",
    ".pytest_cache",
    "__pycache__",
    "deployment",
    "scripts",
    "docs",
    "reference",
    "baseline",
)

# Runtime vars the Streamlit app reads (loaders / ollama_client). When set in the
# deploying machine's environment (e.g. after loading .env), we pass ``-E NAME`` so
# rsconnect copies them onto the Connect content (same as manual -E).
AUTO_FORWARD_ENV_KEYS = (
    "SOCRATA_APP_TOKEN",
    "OLLAMA_API_KEY",
    "OPENAI_API_KEY",
    "OPENAI_MODEL",
)


def _tool_v2_root() -> Path:
    return Path(__file__).resolve().parent.parent


def _load_dotenv() -> None:
    """Load repo root and Tool V3 ``.env`` if ``python-dotenv`` is installed."""
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    root = _tool_v2_root()
    load_dotenv(root.parent / ".env")
    load_dotenv(root / ".env")


def _resolve_api_key(explicit: str | None) -> str | None:
    if explicit:
        return explicit.strip()
    for key in (
        "CONNECT_API_KEY",
        "POSIT_PUBLISHER_KEY",
        "POSIT_CONNECT_PUBLISHER",
        "RSCONNECT_API_KEY",
    ):
        v = (os.environ.get(key) or "").strip()
        if v:
            return v
    return None


def _resolve_server(cli_server: str | None) -> str:
    if cli_server:
        return cli_server.strip()
    for key in ("CONNECT_SERVER", "POSIT_CONNECT_SERVER"):
        v = (os.environ.get(key) or "").strip()
        if v:
            return v
    return DEFAULT_SERVER


def _rsconnect_prefix() -> list[str]:
    """Use ``python -m rsconnect.main`` so deploy works without ``rsconnect`` on PATH."""
    return [sys.executable, "-m", "rsconnect.main"]


def _env_name_from_e_spec(spec: str) -> str:
    return (spec.split("=", 1)[0] or "").strip()


def merge_connect_runtime_env(user_env: list[str]) -> list[str]:
    """
    Append ``-E NAME`` for app runtime vars that are set locally but not already
    listed in ``user_env``. rsconnect copies the value from the deploy environment.
    """
    claimed = {_env_name_from_e_spec(s) for s in user_env}
    out = list(user_env)
    for key in AUTO_FORWARD_ENV_KEYS:
        if key in claimed:
            continue
        if (os.environ.get(key) or "").strip():
            out.append(key)
    return out


def build_rsconnect_argv(
    *,
    server: str,
    app_dir: Path,
    entrypoint: str,
    python_version: str,
    title: str | None,
    app_id: str | None,
    force_new: bool,
    excludes: list[str],
    env_forwards: list[str],
    no_verify: bool,
    extra_rsconnect_args: list[str],
) -> list[str]:
    cmd: list[str] = [
        *_rsconnect_prefix(),
        "deploy",
        "streamlit",
        "--server",
        server,
        "--entrypoint",
        entrypoint,
        "--override-python-version",
        python_version,
    ]

    if app_id:
        cmd.extend(["--app-id", app_id])
        if title:
            cmd.extend(["--title", title])
    else:
        if title:
            cmd.extend(["--title", title])
        if force_new:
            cmd.append("--new")

    for pattern in excludes:
        cmd.extend(["-x", pattern])
    for env_spec in env_forwards:
        cmd.extend(["-E", env_spec])
    if no_verify:
        cmd.append("--no-verify")

    cmd.append(str(app_dir))
    cmd.extend(extra_rsconnect_args)
    return cmd


def redact_argv_for_print(cmd: list[str]) -> str:
    """Hide API keys and ``-E name=value`` secrets in logged argv."""
    out: list[str] = []
    i = 0
    while i < len(cmd):
        a = cmd[i]
        if a in ("--api-key", "-k") and i + 1 < len(cmd):
            out.extend([a, "<redacted>"])
            i += 2
            continue
        if a == "-E" and i + 1 < len(cmd):
            nxt = cmd[i + 1]
            if "=" in nxt:
                out.extend(["-E", "<redacted>"])
            else:
                out.extend(["-E", nxt])
            i += 2
            continue
        out.append(a)
        i += 1
    return " ".join(out)


def main(argv: list[str] | None = None) -> int:
    _load_dotenv()
    root = _tool_v2_root()
    p = argparse.ArgumentParser(
        description="Deploy Tool V3 Streamlit app to Posit Connect (rsconnect-python)."
    )
    p.add_argument(
        "--server",
        default=None,
        help=f"Posit Connect base URL (default: {DEFAULT_SERVER!r}, or CONNECT_SERVER / POSIT_CONNECT_SERVER).",
    )
    p.add_argument(
        "--app-dir",
        type=Path,
        default=root,
        help="Directory to bundle (default: Tool V3 root).",
    )
    p.add_argument(
        "--entrypoint",
        default="app.py",
        help="Streamlit entry file relative to app-dir (default: app.py).",
    )
    p.add_argument(
        "--python-version",
        default=DEFAULT_PYTHON_VERSION,
        metavar="X.Y",
        help=f"Python version for the Connect bundle (default: {DEFAULT_PYTHON_VERSION}).",
    )
    p.add_argument(
        "--title",
        default=None,
        help="Content title on Connect. Default: DEPLOY_STREAMLIT_TITLE env, else unique title with random suffix.",
    )
    p.add_argument(
        "--app-id",
        default=None,
        help="Existing Connect content GUID to replace. Default: DEPLOY_CONNECT_APP_ID env if set.",
    )
    p.add_argument(
        "--no-new-flag",
        action="store_true",
        help="Do not pass --new (only when not using --app-id; e.g. rely on rsconnect metadata for updates).",
    )
    p.add_argument(
        "--api-key",
        default=None,
        help="API key (otherwise CONNECT_API_KEY, POSIT_PUBLISHER_KEY, POSIT_CONNECT_PUBLISHER, RSCONNECT_API_KEY).",
    )
    p.add_argument(
        "-E",
        "--env",
        action="append",
        default=[],
        metavar="NAME[=VALUE]",
        help="Forward an environment variable to Connect (repeatable). Same as rsconnect -E.",
    )
    p.add_argument(
        "--no-app-env",
        action="store_true",
        help="Do not auto-forward SOCRATA_APP_TOKEN / OLLAMA_API_KEY from this environment.",
    )
    p.add_argument(
        "--no-verify",
        action="store_true",
        help="Skip post-deploy HTTP check (rsconnect --no-verify).",
    )
    p.add_argument(
        "-x",
        "--exclude",
        action="append",
        default=[],
        metavar="GLOB",
        help="Extra glob exclude for the bundle (repeatable). Default excludes always apply.",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the command and exit without deploying.",
    )
    p.add_argument(
        "rsconnect_args",
        nargs=argparse.REMAINDER,
        help="Extra args passed through to `rsconnect deploy streamlit` (use after --).",
    )

    args = p.parse_args(argv)
    app_dir = args.app_dir.resolve()
    if not app_dir.is_dir():
        print(f"ERROR: app directory not found: {app_dir}", file=sys.stderr)
        return 2

    server = _resolve_server(args.server).rstrip("/") + "/"

    api_key = _resolve_api_key(args.api_key)
    if not args.dry_run and not api_key:
        print(
            "ERROR: No API key. Set CONNECT_API_KEY, POSIT_PUBLISHER_KEY, POSIT_CONNECT_PUBLISHER, "
            "or RSCONNECT_API_KEY in .env, or pass --api-key.",
            file=sys.stderr,
        )
        return 2

    app_id = (args.app_id or os.environ.get("DEPLOY_CONNECT_APP_ID") or "").strip() or None

    if app_id:
        force_new = False
    else:
        force_new = not args.no_new_flag

    title = args.title
    if title is None:
        title = (os.environ.get("DEPLOY_STREAMLIT_TITLE") or "").strip() or None
    if not app_id and title is None:
        suffix = uuid.uuid4().hex[:8]
        title = f"Measles Risk Tool V3 [{suffix}]"

    excludes = list(dict.fromkeys([*DEFAULT_EXCLUDES, *args.exclude]))

    extra = list(args.rsconnect_args or [])
    if extra and extra[0] == "--":
        extra = extra[1:]

    env_forwards = list(args.env)
    if not args.no_app_env:
        env_forwards = merge_connect_runtime_env(env_forwards)

    cmd = build_rsconnect_argv(
        server=server,
        app_dir=app_dir,
        entrypoint=args.entrypoint,
        python_version=args.python_version,
        title=title,
        app_id=app_id,
        force_new=force_new,
        excludes=excludes,
        env_forwards=env_forwards,
        no_verify=args.no_verify,
        extra_rsconnect_args=extra,
    )

    env = os.environ.copy()
    if api_key:
        env["CONNECT_API_KEY"] = api_key
    env.setdefault("CONNECT_SERVER", server.rstrip("/"))

    if args.dry_run:
        print("Dry run - command that would be executed:")
        print(" ", redact_argv_for_print(cmd))
        print("\nEnvironment: CONNECT_API_KEY=<set>" if api_key else "\nEnvironment: CONNECT_API_KEY=<missing>")
        print(f"Working directory: {app_dir}")
        return 0

    print("Deploying to", server)
    print(" ", redact_argv_for_print(cmd))
    proc = subprocess.run(cmd, cwd=str(app_dir), env=env)
    return int(proc.returncode)


if __name__ == "__main__":
    raise SystemExit(main())
