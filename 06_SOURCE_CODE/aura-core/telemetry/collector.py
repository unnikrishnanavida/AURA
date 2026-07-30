from __future__ import annotations

from .metrics import Metrics


class Collector:
    def __init__(self) -> None:
        self._metrics = Metrics()

    @property
    def metrics(self) -> Metrics:
        return self._metrics
