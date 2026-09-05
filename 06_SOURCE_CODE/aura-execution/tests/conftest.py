"""Pytest bootstrap: make the ``src``-layout package importable.

The other AURA repos that use ``src/`` layout do this per test file; this
conftest centralizes it for every test in aura-execution without touching
production code.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))