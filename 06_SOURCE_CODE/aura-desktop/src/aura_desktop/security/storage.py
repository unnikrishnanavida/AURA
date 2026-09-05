"""Secure local storage abstraction for aura-desktop.

An INTERFACE (not a real OS keychain): the base class defines the contract;
the in-memory store is a deterministic implementation suitable for tests and
unsandboxed prototypes. A production implementation would back this with the
platform keychain/credential store — that is explicitly NOT claimed here.
"""

from __future__ import annotations

import abc
from typing import Any


class SecureLocalStorage(abc.ABC):
    """Contract for secure local persistence of small secrets/settings."""

    @abc.abstractmethod
    def get(self, key: str) -> Any | None: ...

    @abc.abstractmethod
    def set(self, key: str, value: Any) -> None: ...

    @abc.abstractmethod
    def delete(self, key: str) -> bool: ...


class InMemorySecureStorage(SecureLocalStorage):
    """Deterministic in-memory implementation labeled SIMULATION/INTERFACE."""

    kind = "memory"

    def __init__(self) -> None:
        self._data: dict[str, Any] = {}

    def get(self, key: str) -> Any | None:
        return self._data.get(key)

    def set(self, key: str, value: Any) -> None:
        self._data[key] = value

    def delete(self, key: str) -> bool:
        return self._data.pop(key, None) is not None


__all__ = ["InMemorySecureStorage", "SecureLocalStorage"]