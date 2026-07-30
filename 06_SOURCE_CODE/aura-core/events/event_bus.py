from __future__ import annotations

from collections import defaultdict
from typing import Callable, Dict, List

from .event import Event


class EventBus:
    def __init__(self) -> None:
        self._subscribers: Dict[str, List[Callable[[Event], None]]] = defaultdict(list)

    def subscribe(self, event_name: str, handler: Callable[[Event], None]) -> None:
        self._subscribers[event_name].append(handler)

    def publish(self, event: Event) -> None:
        for h in list(self._subscribers.get(event.name, [])):
            h(event)
