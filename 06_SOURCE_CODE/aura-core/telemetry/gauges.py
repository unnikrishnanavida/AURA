from __future__ import annotations

from .metrics import Metrics


class Gauge:
    def __init__(self, metrics: Metrics, name: str) -> None:
        self.metrics = metrics
        self.name = name

    def set(self, value: float) -> None:
        self.metrics.set_gauge(self.name, value)
