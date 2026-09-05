"""Sync client for aura-mobile: offline-first request tracking.

When offline, requests go to the queue; when online, queued requests are
flushed through the network layer. Contracts only; no real transport claimed.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from aura_mobile.network.resilience import InMemoryNetwork, NetworkResilience
from aura_mobile.offline.queue import OfflineQueue, QueuedRequest


@dataclass
class SyncClient:
    """Offline-first client that queues requests and flushes on reconnect."""

    network: NetworkResilience = field(default_factory=InMemoryNetwork)
    queue: OfflineQueue = field(default_factory=OfflineQueue)

    def send(self, method: str, path: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        if self.network.is_online():
            return self.network.request(method, path, **(payload or {}))
        self.queue.enqueue(method, path, payload or {})
        return {"queued": True, "path": path, "method": method}

    def sync(self) -> dict[str, Any]:
        """Flush queued requests; returns a sync summary."""
        initially = len(self.queue)

        def deliver(item: QueuedRequest) -> bool:
            self.network.request(item.method, item.path, **(item.payload or {}))
            return True

        remaining = self.queue.flush(deliver)
        return {
            "queued_before": initially,
            "delivered": initially - len(remaining),
            "undelivered": len(remaining),
        }


__all__ = ["SyncClient"]