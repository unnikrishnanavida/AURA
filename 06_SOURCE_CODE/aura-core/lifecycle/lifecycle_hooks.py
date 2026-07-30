from __future__ import annotations

from typing import Callable, List


class LifecycleHooks:
    def __init__(self) -> None:
        self._on_start: List[Callable] = []
        self._on_stop: List[Callable] = []

    def on_start(self, fn: Callable) -> None:
        self._on_start.append(fn)

    def on_stop(self, fn: Callable) -> None:
        self._on_stop.append(fn)

    def run_start(self) -> None:
        for f in self._on_start:
            f()

    def run_stop(self) -> None:
        for f in self._on_stop:
            f()
