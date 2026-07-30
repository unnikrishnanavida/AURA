from __future__ import annotations

from typing import Dict, List, Callable


class EventRegistry:
    def __init__(self) -> None:
        self._listeners: Dict[str, List[Callable]] = {}

    def register(self, event_name: str, handler: Callable) -> None:
        self._listeners.setdefault(event_name, []).append(handler)

    def get(self, event_name: str):
        return list(self._listeners.get(event_name, []))
