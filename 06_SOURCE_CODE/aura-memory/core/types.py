"""Core type aliases and protocols."""

from __future__ import annotations

from typing import Any, Dict, Iterable, Mapping, MutableMapping

JSON = Dict[str, Any]
JSONLike = Mapping[str, Any]
Key = str
Value = Any

__all__ = ["JSON", "JSONLike", "Key", "Value"]
