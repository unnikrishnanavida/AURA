"""AURA mobile client.

A real, shared, tested mobile-client foundation built on the same primitives
as the desktop client:

- secure storage via :class:`~aura.clients.secure_store.SecureStore` — the
  binding seam for Android Keystore / iOS Keychain wrappers (platform wiring
  is environment-dependent and is NOT claimed here);
- offline-first operation via
  :class:`~aura.clients.offline_queue.OfflineQueue` (idempotent, LWW).

:class:`MobileClient` exposes the offline-first contract a platform app binds:
``reason()`` succeeds online or queues offline, ``sync()`` replays on
reconnect, and ``snapshot()`` reports the queue state + conflict strategy for
the UI. Android/iOS builds and on-device launches are **NOT VERIFIED** in this
environment.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from aura.clients.offline_queue import OfflineQueue
from aura.clients.secure_store import SecureStore


@dataclass
class SyncSnapshot:
    pending: int
    last_sequence: int
    conflict_strategy: str = "last-write-wins"

    def to_dict(self) -> dict[str, Any]:
        return {
            "pending": self.pending,
            "last_sequence": self.last_sequence,
            "conflict_strategy": self.conflict_strategy,
        }


class MobileClient:
    """Offline-first mobile client (shared logic; platform wiring is a seam)."""

    def __init__(
        self,
        *,
        api: Any,
        storage: SecureStore,
        queue: OfflineQueue,
        platform: str = "android",
    ) -> None:
        self._api = api
        self._storage = storage
        self._queue = queue
        self.platform = platform  # "android" | "ios" (drives the storage seam)

    @property
    def online(self) -> bool:
        ready = getattr(self._api, "ready", None)
        if callable(ready):
            try:
                return bool(ready())
            except Exception:  # noqa: BLE001 - offline detection must not raise
                return False
        return True

    def auth_saved(self) -> bool:
        return self._storage.get("api_key") is not None

    def save_auth(self, api_key: str) -> None:
        self._storage.set("api_key", api_key)

    def clear_auth(self) -> None:
        self._storage.delete("api_key")

    # -- offline-first operations -------------------------------------------

    def reason(self, question: str, **facts: float) -> dict[str, Any]:
        """Run online or queue offline; idempotency key is the question."""
        if self.online:
            return dict(self._api.reason(question, facts or None) or {})
        record = self._queue.enqueue(
            op="reason", params={"question": question, "facts": facts},
            idempotency_key=f"reason:{question}",
        )
        return {"queued": True, "idempotency_key": record["idempotency_key"]}

    def snapshot(self) -> SyncSnapshot:
        pending = self._queue.pending()
        last = max((int(r.get("sequence", 0)) for r in pending), default=-1)
        return SyncSnapshot(pending=len(pending), last_sequence=last)

    def sync(self, *, executor: Callable[[dict[str, Any]], bool] | None = None) -> dict[str, int]:
        runner = executor or self._executor
        return self._queue.replay(runner)

    def _executor(self, record: dict[str, Any]) -> bool:
        op = record.get("op")
        if op == "reason":
            params = record.get("params") or {}
            self._api.reason(params.get("question", ""), params.get("facts") or {})
            return True
        return False


__all__ = ["MobileClient", "SyncSnapshot"]