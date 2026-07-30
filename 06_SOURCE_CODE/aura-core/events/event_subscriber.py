from __future__ import annotations

from typing import Callable


class EventSubscriber:
    def __init__(self, handler: Callable) -> None:
        self.handler = handler

    def notify(self, event) -> None:
        self.handler(event)
