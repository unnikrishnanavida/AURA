from __future__ import annotations

from .event_dispatcher import EventDispatcher


class EventPublisher:
    def __init__(self, dispatcher: EventDispatcher) -> None:
        self._dispatcher = dispatcher

    def publish(self, name: str, payload: dict) -> None:
        self._dispatcher.dispatch(name, payload)
