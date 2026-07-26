"""Event primitives for the kernel subsystem."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable


@dataclass(slots=True)
class KernelEvent:
    """A simple domain event."""

    type: str
    payload: dict[str, Any] = field(default_factory=dict)


class KernelEventBus:
    """Minimal event bus for kernel events."""

    def __init__(self) -> None:
        self._listeners: dict[str, list[Callable[[KernelEvent], None]]] = {}

    def subscribe(self, event_type: str, listener: Callable[[KernelEvent], None]) -> None:
        """Register a listener for an event type."""
        self._listeners.setdefault(event_type, []).append(listener)

    def publish(self, event: KernelEvent) -> None:
        """Publish an event."""
        for listener in self._listeners.get(event.type, []):
            listener(event)
