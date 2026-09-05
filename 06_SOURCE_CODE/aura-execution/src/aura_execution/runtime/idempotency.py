"""Idempotency for aura-execution.

Re-running the same logical action with the same idempotency key must produce
the recorded result instead of re-executing the side effect. Idempotency keys
are checked BEFORE dispatch and results are memoized AFTER success.
"""

from __future__ import annotations

import threading
from dataclasses import dataclass, field
from typing import Any


@dataclass
class IdempotencyStore:
    """In-memory idempotency key -> recorded outcome."""

    _records: dict[str, dict[str, Any]] = field(default_factory=dict)
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def get(self, key: str) -> dict[str, Any] | None:
        with self._lock:
            return self._records.get(key)

    def put(self, key: str, outcome: dict[str, Any]) -> None:
        with self._lock:
            self._records[key] = outcome

    def has(self, key: str) -> bool:
        with self._lock:
            return key in self._records


class IdempotencyGuard:
    """Wraps the execute path: dedupe on key, memoize on success."""

    def __init__(self, store: IdempotencyStore | None = None) -> None:
        self.store = store or IdempotencyStore()

    def execute(self, key: str, fn):
        prior = self.store.get(key)
        if prior is not None:
            return dict(prior)  # replayed: same outcome, no side effect
        outcome = fn()
        if outcome.get("success", False):
            self.store.put(key, outcome)
        return outcome


__all__ = ["IdempotencyGuard", "IdempotencyStore"]