"""Ensure ``Tool V3/`` is on ``sys.path`` for ``loaders``, ``tools``, ``contracts``."""
from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

try:
    from dotenv import load_dotenv

    load_dotenv(_ROOT.parent / ".env")
    load_dotenv(_ROOT / ".env")
except ImportError:
    pass
