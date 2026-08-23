"""Monitoring helpers for aura-memory."""

from __future__ import annotations

import threading
from collections import Counter
from typing import Any, Dict, Optional


class MetricsRegistry:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._counters: Counter[str] = Counter()
        self._gauges: Dict[str, Any] = {}

    def increment(self, name: str, amount: int = 1) -> None:
        with self._lock:
            self._counters[name] += amount

    def set_gauge(self, name: str, value: Any) -> None:
        with self._lock:
            self._gauges[name] = value

    def snapshot(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "counters": dict(self._counters),
                "gauges": dict(self._gauges),
            }

    def clear(self) -> None:
        with self._lock:
            self._counters.clear()
            self._gauges.clear()


metrics = MetricsRegistry()


def increment(name: str, amount: int = 1) -> None:
    metrics.increment(name, amount)


def set_gauge(name: str, value: Any) -> None:
    metrics.set_gauge(name, value)


def snapshot() -> Dict[str, Any]:
    return metrics.snapshot()


__all__ = ["MetricsRegistry", "metrics", "increment", "set_gauge", "snapshot"]
