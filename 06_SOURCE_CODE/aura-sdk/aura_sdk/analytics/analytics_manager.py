"""AURA SDK Analytics analytics_manager.

Minimal analytics manager with a lightweight event recorder. This is
kept intentionally small: production implementations should extend
this class and provide persistence, batching, and backend integrations.
"""

from typing import Any, Dict


class AnalyticsManager:
    """Manager for aura_sdk.analytics.analytics_manager."""

    def __init__(self) -> None:
        self._events: Dict[str, Any] = {}

    def record(self, name: str, payload: Any) -> None:
        if not name:
            raise ValueError("event name must be non-empty")
        self._events.setdefault(name, []).append(payload)

    def get_events(self, name: str):
        return list(self._events.get(name, []))

    def clear(self) -> None:
        self._events.clear()
