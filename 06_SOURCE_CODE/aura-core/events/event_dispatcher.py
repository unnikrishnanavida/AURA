from __future__ import annotations

from .event_bus import EventBus
from .event import Event


class EventDispatcher:
    def __init__(self, bus: EventBus) -> None:
        self.bus = bus

    def dispatch(self, name: str, payload: dict) -> None:
        self.bus.publish(Event(name, payload))
