"""In-process event bus for SDK streaming.

The bus delivers local events to registered subscribers synchronously (cheap,
deterministic). It powers streaming use-cases in local mode (e.g. pipeline stage
progress, reflection signals). Remote streaming via server-sent events is
outside the current transport surface and is documented as a limitation, not
silently emulated.
"""

from __future__ import annotations

import threading
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True, slots=True)
class SdkEvent:
    event_type: str
    payload: dict[str, Any] = field(default_factory=dict)
    trace_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {"event_type": self.event_type, "payload": self.payload, "trace_id": self.trace_id}


class EventBus:
    """Synchronous local event distribution to registered subscribers."""

    def __init__(self) -> None:
        self._subscribers: list[Callable[[SdkEvent], None]] = []
        self._lock = threading.RLock()

    def subscribe(self, handler: Callable[[SdkEvent], None]) -> Callable[[SdkEvent], None]:
        with self._lock:
            self._subscribers.append(handler)
        return handler

    def unsubscribe(self, handler: Callable[[SdkEvent], None]) -> None:
        with self._lock:
            if handler in self._subscribers:
                self._subscribers.remove(handler)

    def publish(self, event: SdkEvent) -> None:
        with self._lock:
            subscribers = list(self._subscribers)
        for handler in subscribers:
            handler(event)

    def count(self) -> int:
        with self._lock:
            return len(self._subscribers)


__all__ = ["EventBus", "SdkEvent"]