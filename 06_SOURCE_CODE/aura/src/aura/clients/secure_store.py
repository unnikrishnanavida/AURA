"""Secure storage abstraction for desktop/mobile clients.

Never plaintext-on-disk by design:

- :class:`SecureStore` (protocol): get / set / delete / reset.
- :class:`MemorySecureStore` — test-only, in-memory.
- :class:`EnvVarSecureStore` — reads values from environment variables
  (non-persistent, no plaintext file).
- :class:`KeyringSecureStore` — REAL OS keychain via the ``keyring`` package
  (Windows Credential Manager / macOS Keychain / Linux Secret Service). Raises
  :class:`ConfigurationError` when ``keyring`` is unavailable rather than
  silently degrading to plaintext.

There is deliberately NO plaintext-file backend.
"""

from __future__ import annotations

import os
from typing import Protocol

from aura.foundation.errors import ConfigurationError


class SecureStore(Protocol):
    def get(self, key: str) -> str | None: ...
    def set(self, key: str, value: str) -> None: ...
    def delete(self, key: str) -> None: ...
    def reset(self) -> None: ...


class MemorySecureStore:
    """Test-only in-memory store (never persisted)."""

    def __init__(self) -> None:
        self._data: dict[str, str] = {}

    def get(self, key: str) -> str | None:
        return self._data.get(key)

    def set(self, key: str, value: str) -> None:
        self._data[key] = value

    def delete(self, key: str) -> None:
        self._data.pop(key, None)

    def reset(self) -> None:
        self._data.clear()


class EnvVarSecureStore:
    """Environment-variable-backed store (non-persistent, no plaintext file)."""

    def __init__(self, *, prefix: str = "AURA_CLIENT_") -> None:
        self._prefix = prefix

    def _key(self, key: str) -> str:
        return self._prefix + key.upper()

    def get(self, key: str) -> str | None:
        return os.environ.get(self._key(key))

    def set(self, key: str, value: str) -> None:
        os.environ[self._key(key)] = value

    def delete(self, key: str) -> None:
        os.environ.pop(self._key(key), None)

    def reset(self) -> None:
        for name in [n for n in os.environ if n.startswith(self._prefix)]:
            os.environ.pop(name, None)


class KeyringSecureStore:
    """Real OS keychain via ``keyring``; refuses to fall back to plaintext."""

    service = "aura-desktop"

    def __init__(self, *, service: str = "aura-desktop") -> None:
        self.service = service
        try:
            import keyring  # type: ignore[import-not-found]  # noqa: F401
        except ImportError as exc:
            raise ConfigurationError(
                "keyring is not installed; refusing plaintext secret storage (pip install keyring)"
            ) from exc

    def get(self, key: str) -> str | None:
        import keyring

        return keyring.get_password(self.service, key)  # type: ignore[no-any-return]

    def set(self, key: str, value: str) -> None:
        import keyring

        keyring.set_password(self.service, key, value)

    def delete(self, key: str) -> None:
        import keyring

        try:
            keyring.delete_password(self.service, key)
        except Exception:  # noqa: BLE001 - deleting a missing entry is a no-op
            return

    def reset(self) -> None:
        # Keychains are not enumerable without a store listing; delete known keys.
        for known in ("api_key", "endpoint"):
            self.delete(known)


def secure_store_from(kind: str, **kwargs: object) -> SecureStore:
    """Factory: ``memory`` | ``env`` | ``keyring`` (never plaintext)."""
    normalized = kind.strip().lower()
    if normalized == "memory":
        return MemorySecureStore()
    if normalized == "env":
        return EnvVarSecureStore(**kwargs)  # type: ignore[arg-type]
    if normalized == "keyring":
        return KeyringSecureStore(**kwargs)  # type: ignore[arg-type]
    raise ConfigurationError(f"unknown secure store kind {kind!r}")


__all__ = [
    "EnvVarSecureStore",
    "KeyringSecureStore",
    "MemorySecureStore",
    "SecureStore",
    "secure_store_from",
]