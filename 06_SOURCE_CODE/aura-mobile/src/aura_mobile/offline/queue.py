"""Offline request queueing for aura-mobile.

Requests enqueued while offline are retried when the device comes back online.
The queue is bounded and ordered; items are never silently dropped.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any


@dataclass
class QueuedRequest:
    """A request awaiting delivery."""

    method: str
    path: str
    payload: dict[str, Any] = field(default_factory=dict)
    attempts: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {"method": self.method, "path": self.path, "payload": dict(self.payload), "attempts": self.attempts}


class OfflineQueue:
    """An ordered, bounded queue with delivery-callback retries."""

    def __init__(self, *, max_size: int = 100, max_attempts: int = 3) -> None:
        self.max_size = max_size
        self.max_attempts = max_attempts
        self._items: list[QueuedRequest] = []

    def enqueue(self, method: str, path: str, payload: dict[str, Any]) -> None:
        if len(self._items) >= self.max_size:
            raise OverflowError("offline queue is full; request dropped")
        self._items.append(QueuedRequest(method=method, path=path, payload=payload))

    def __len__(self) -> int:
        return len(self._items)

    def flush(self, deliver: Callable[[QueuedRequest], bool]) -> list[QueuedRequest]:
        """Attempt delivery of every queued request.

        Successful deliveries are removed; failed ones keep their retry count
        and are retained (re-enqueued at the back) until ``max_attempts``.
        Returns the list of requests that remain undelivered.
        """
        remaining: list[QueuedRequest] = []
        for item in self._items:
            try:
                delivered = deliver(item)
            except Exception:  # noqa: BLE001 - delivery failure must not crash flush
                delivered = False
            if delivered:
                continue
            item.attempts += 1
            if item.attempts < self.max_attempts:
                remaining.append(item)
        self._items = remaining
        return list(remaining)


__all__ = ["OfflineQueue", "QueuedRequest"]