from __future__ import annotations

from typing import Callable


class LifecycleObserver:
    def __init__(self, on_event: Callable[[str], None]) -> None:
        self.on_event = on_event

    def notify(self, event_name: str) -> None:
        self.on_event(event_name)
