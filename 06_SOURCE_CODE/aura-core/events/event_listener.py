from __future__ import annotations

from typing import Callable


class EventListener:
    def __init__(self, event_name: str, handler: Callable) -> None:
        self.event_name = event_name
        self.handler = handler
