"""Idempotency and structured-result contracts for aura-core."""

from __future__ import annotations

import threading
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any


class DuplicateKeyError(KeyError):
    """Raised when an idempotency key is re-used for a different logical op."""


class IdempotencyStore:
    """Thread-safe in-memory idempotency key -> recorded outcome."""

    def __init__(self) -> None:
        self._records: dict[str, dict[str, Any]] = {}
        self._lock = threading.Lock()

    def set(self, key: str, outcome: dict[str, Any], *, overwrite: bool = False) -> None:
        with self._lock:
            if not overwrite and key in self._records:
                raise DuplicateKeyError(f"idempotency key {key!r} already recorded")
            self._records[key] = outcome

    def get(self, key: str) -> dict[str, Any] | None:
        with self._lock:
            return self._records.get(key)

    def has(self, key: str) -> bool:
        with self._lock:
            return key in self._records


@dataclass(frozen=True)
class IdempotencyRecord:
    key: str
    outcome: dict[str, Any] = field(default_factory=dict)
    replayed: bool = False


class IdempotentExecutor:
    """Wraps a callable so retries return the recorded outcome."""

    def __init__(self, store: IdempotencyStore | None = None) -> None:
        self.store = store or IdempotencyStore()

    def execute(self, key: str, fn: Callable[[], dict[str, Any]]) -> IdempotencyRecord:
        prior = self.store.get(key)
        if prior is not None:
            return IdempotencyRecord(key=key, outcome=dict(prior), replayed=True)
        outcome = fn()
        self.store.set(key, outcome)
        return IdempotencyRecord(key=key, outcome=outcome, replayed=False)


__all__ = ["DuplicateKeyError", "IdempotencyRecord", "IdempotencyStore", "IdempotentExecutor"]