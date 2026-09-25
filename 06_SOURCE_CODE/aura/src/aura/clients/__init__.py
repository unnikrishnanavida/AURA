"""Thick clients (desktop/mobile foundations).

Shared, genuinely tested primitives for product clients:

- :mod:`aura.clients.secure_store` — never-plaintext secret storage backends
  (memory for tests, env, OS keyring).
- :mod:`aura.clients.offline_queue` — durable idempotent offline operation
  queue with retry and last-write-wins conflict handling.
- :mod:`aura.clients.desktop` — desktop client (lifecycle + online/offline
  operation with secure storage and queue replay).
- :mod:`aura.clients.mobile` (Phase 34) — mobile client contract on the same
  primitives.
"""

from aura.clients.desktop import AppState, DesktopClient, DesktopLifecycle
from aura.clients.offline_queue import OfflineQueue
from aura.clients.secure_store import (
    EnvVarSecureStore,
    KeyringSecureStore,
    MemorySecureStore,
    SecureStore,
    secure_store_from,
)

__all__ = [
    "AppState",
    "DesktopClient",
    "DesktopLifecycle",
    "EnvVarSecureStore",
    "KeyringSecureStore",
    "MemorySecureStore",
    "OfflineQueue",
    "SecureStore",
    "secure_store_from",
]