"""Cancellation and timeout contracts for aura-core.

Cooperative cancellation + deterministic timeouts, both injectable and
dependency-free.
"""

from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Any


class Cancelled(Exception):
    """Raised when an operation is cancelled."""


class CancellationToken:
    """A cooperative, thread-safe cancellation signal."""

    def __init__(self) -> None:
        self._cancelled = False
        self._lock = threading.Lock()

    def cancel(self) -> None:
        with self._lock:
            self._cancelled = True

    @property
    def cancelled(self) -> bool:
        with self._lock:
            return self._cancelled

    def check(self) -> None:
        if self.cancelled:
            raise Cancelled()


class TimeoutGuard:
    """Runs a callable and reports whether it exceeded a budget."""

    def __init__(self, timeout_seconds: float) -> None:
        if timeout_seconds <= 0:
            raise ValueError("timeout must be positive")
        self.timeout_seconds = timeout_seconds

    def run(self, fn: Any, *args: Any, **kwargs: Any) -> tuple[float, Any]:
        started = time.monotonic()
        value = fn(*args, **kwargs)
        elapsed = time.monotonic() - started
        return elapsed, value

    def exceeded(self, elapsed: float) -> bool:
        return elapsed > self.timeout_seconds


@dataclass
class TimeoutResult:
    """Outcome of a timed operation."""

    ok: bool
    value: Any = None
    elapsed: float = 0.0

    @property
    def timed_out(self) -> bool:
        return not self.ok


__all__ = ["CancellationToken", "Cancelled", "TimeoutGuard", "TimeoutResult"]