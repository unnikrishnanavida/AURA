"""AURA desktop client.

A real thick-client foundation (no GUI framework required for the logic):

- :class:`DesktopLifecycle` — STOPPED → STARTING → READY → (OFFLINE) →
  STOPPING, with hooks.
- :class:`DesktopClient` — authenticates against the AURA API with a
  :class:`~aura.clients.secure_store.SecureStore` (never plaintext), calls the
  SDK/API when online, and queues operations offline for later replay via
  :class:`~aura.clients.offline_queue.OfflineQueue` (idempotent, LWW).
  :meth:`sync` replays queued operations after reconnection.

Packaging (Windows/macOS/Linux installers, DPAPI/Keychain/Secret-Service
wiring) is **environment-dependent**; the logic below is unit-tested.
"""

from __future__ import annotations

from collections.abc import Callable
from enum import StrEnum
from typing import Any

from aura.clients.offline_queue import OfflineQueue
from aura.clients.secure_store import SecureStore
from aura.foundation.clock import Clock, SystemClock


class AppState(StrEnum):
    STOPPED = "stopped"
    STARTING = "starting"
    READY = "ready"
    OFFLINE = "offline"
    STOPPING = "stopping"


class DesktopLifecycle:
    def __init__(self, *, on_state: Callable[[AppState], None] | None = None) -> None:
        self._state = AppState.STOPPED
        self._hook = on_state

    @property
    def state(self) -> AppState:
        return self._state

    def start(self) -> AppState:
        self._set(AppState.STARTING)
        self._set(AppState.READY)
        return self._state

    def go_offline(self) -> AppState:
        if self._state in {AppState.READY, AppState.OFFLINE}:
            self._set(AppState.OFFLINE)
        return self._state

    def reconnect(self) -> AppState:
        if self._state is AppState.OFFLINE:
            self._set(AppState.READY)
        return self._state

    def stop(self) -> AppState:
        if self._state not in {AppState.STOPPED, AppState.STOPPING}:
            self._set(AppState.STOPPING)
            self._set(AppState.STOPPED)
        return self._state

    def _set(self, state: AppState) -> None:
        self._state = state
        if self._hook is not None:
            with __import__("contextlib").suppress(Exception):
                self._hook(state)


class DesktopClient:
    """Online/offline AURA client using secure storage and an idempotent queue."""

    def __init__(
        self,
        *,
        api: Any,
        storage: SecureStore,
        queue: OfflineQueue,
        clock: Clock | None = None,
        lifecycle: DesktopLifecycle | None = None,
    ) -> None:
        self._api = api
        self._storage = storage
        self._queue = queue
        self._clock = clock or SystemClock()
        self.lifecycle = lifecycle or DesktopLifecycle()

    # -- authentication -----------------------------------------------------

    def is_authenticated(self) -> bool:
        return self._storage.get("api_key") is not None

    def authenticate(self, api_key: str) -> bool:
        """Verify against the API and store the key securely (never plaintext)."""
        if self.lifecycle.state is AppState.STOPPED:
            self.lifecycle.start()
        self._api.config = {**getattr(self._api, "config", {}), "apiKey": api_key}
        ready = self._api.ready
        ok = bool(ready())
        if ok:
            self._storage.set("api_key", api_key)
            self.lifecycle.reconnect()
        return ok

    def sign_out(self) -> None:
        self._storage.delete("api_key")

    # -- operations -----------------------------------------------------------

    def reason(self, question: str, **facts: float) -> dict[str, Any]:
        if self.lifecycle.state is AppState.READY:
            result = self._api.reason(question, facts or None)
            self.lifecycle.reconnect()
            return dict(result or {})
        record = self._queue.enqueue(
            op="reason", params={"question": question, "facts": facts},
            idempotency_key=f"reason:{question}",
        )
        return {"queued": True, "idempotency_key": record["idempotency_key"]}

    def sync(self, *, executor: Callable[[dict[str, Any]], bool] | None = None) -> dict[str, int]:
        """Replay queued operations; returns replay counters."""
        runner = executor or self._executor
        result = self._queue.replay(runner)
        if result["replayed"]:
            self.lifecycle.reconnect()
        return result

    def _executor(self, record: dict[str, Any]) -> bool:
        op = record.get("op")
        if op == "reason":
            params = record.get("params") or {}
            self._api.reason(params.get("question", ""), params.get("facts") or {})
            return True
        return False


__all__ = ["AppState", "DesktopClient", "DesktopLifecycle"]