"""Timeout enforcement for aura-execution.

Wraps action handlers so they fail fast with a classified *timeout* failure
when they exceed their time budget. Deterministic and injectable for tests.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any


class TimeoutError(Exception):
    """Raised when an action exceeds its time budget."""


@dataclass
class TimeoutGuard:
    """Enforces a time budget around a callable."""

    timeout: float
    clock: Any = time

    def run(self, fn, *args: Any, **kwargs: Any) -> tuple[float, Any]:
        """Run ``fn`` and raise TimeoutError when it exceeds the budget.

        The guard is best-effort for synchronous handlers: it monitors elapsed
        time and raises if the budget is exceeded. Cooperative handlers may
        also check :meth:`elapsed_seconds`.
        """
        started = self.clock.monotonic()
        result = fn(*args, **kwargs)
        elapsed = self.clock.monotonic() - started
        if elapsed > self.timeout:
            raise TimeoutError(f"action exceeded time budget of {self.timeout:g}s")
        return elapsed, result


__all__ = ["TimeoutError", "TimeoutGuard"]