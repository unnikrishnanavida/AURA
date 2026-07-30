from __future__ import annotations

from typing import Protocol


class EventHandlerProtocol(Protocol):
    def handle(self, event) -> None: ...
