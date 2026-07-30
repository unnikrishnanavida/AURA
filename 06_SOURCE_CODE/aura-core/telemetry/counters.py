from __future__ import annotations

from .metrics import Metrics


class Counter:
    def __init__(self, metrics: Metrics, name: str) -> None:
        self.metrics = metrics
        self.name = name

    def inc(self, n: int = 1) -> None:
        self.metrics.inc(self.name, n)
