"""Networking helpers for AURA Memory."""

from __future__ import annotations

from typing import Any, Dict


class NetworkEngine:
    """Basic networking abstraction for AURA Memory."""

    def request(self, endpoint: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        if not endpoint:
            raise ValueError("endpoint must be non-empty")
        if not isinstance(payload, dict):
            raise TypeError("payload must be a dict")
        return {"endpoint": endpoint, "payload": payload, "status": "ok"}


__all__ = ["NetworkEngine"]
