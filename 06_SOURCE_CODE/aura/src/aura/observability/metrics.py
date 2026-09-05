"""Metrics.

Thread-safe counters, gauges, and timers. The metrics registry is the single
source for execution count, success/failure rate, latency, retries, recovery,
budget consumption, tool and provider failures.
"""

from __future__ import annotations

import threading
import time
from collections import defaultdict
from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any


class Metrics:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._counters: dict[str, int] = defaultdict(int)
        self._gauges: dict[str, float] = {}
        self._latency: dict[str, list[float]] = defaultdict(list)

    def increment(self, name: str, *, labels: dict[str, str] | None = None, amount: int = 1) -> None:
        key = _key(name, labels)
        with self._lock:
            self._counters[key] += amount

    def set_gauge(self, name: str, value: float, *, labels: dict[str, str] | None = None) -> None:
        with self._lock:
            self._gauges[_key(name, labels)] = value

    def observe(self, name: str, seconds: float, *, labels: dict[str, str] | None = None) -> None:
        with self._lock:
            self._latency[_key(name, labels)].append(seconds)

    @contextmanager
    def timed(self, name: str, *, labels: dict[str, str] | None = None) -> Iterator[None]:
        started = time.monotonic()
        try:
            yield
        finally:
            self.observe(name, time.monotonic() - started, labels=labels)

    def count(self, name: str, labels: dict[str, str] | None = None) -> int:
        return self._counters[_key(name, labels)]

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            counters = {k: v for k, v in sorted(self._counters.items())}
            gauges = {k: v for k, v in sorted(self._gauges.items())}
            latency: dict[str, Any] = {}
            for key, values in sorted(self._latency.items()):
                if values:
                    latency[key] = {
                        "count": len(values),
                        "avg_seconds": round(sum(values) / len(values), 6),
                        "max_seconds": round(max(values), 6),
                    }
            return {"counters": counters, "gauges": gauges, "latency": latency}


class TimerContext:
    """Standalone timer object usable without a Metrics instance."""

    def __init__(self) -> None:
        self._started = time.monotonic()

    def elapsed(self) -> float:
        return time.monotonic() - self._started


def _key(name: str, labels: dict[str, str] | None) -> str:
    if not labels:
        return name
    return name + "{" + ",".join(f"{k}={v}" for k, v in sorted(labels.items())) + "}"


__all__ = ["Metrics", "TimerContext"]