"""Serialization helpers for aura-memory."""

import json
from typing import Any, Dict


def safe_dumps(obj: Any) -> str:
    return json.dumps(obj, default=str, separators=(",", ":"))


def safe_loads(s: str) -> Dict[str, Any]:
    return json.loads(s)


__all__ = ["safe_dumps", "safe_loads"]
