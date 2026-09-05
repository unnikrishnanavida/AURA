"""Secure token/credential storage abstraction for aura-mobile.

INTERFACE: the base class defines the contract; the in-memory store is a
deterministic test/runtime double. No real Android/iOS Keychain/Keystore
integration is claimed. Production builds MUST back this with the platform
secure storage.
"""

from __future__ import annotations

import abc


class SecureCredentialStore(abc.ABC):
    """Contract for secure storage of tokens/credentials."""

    @abc.abstractmethod
    def save_token(self, name: str, token: str) -> None: ...

    @abc.abstractmethod
    def read_token(self, name: str) -> str | None: ...

    @abc.abstractmethod
    def delete_token(self, name: str) -> bool: ...


class InMemorySecureCredentialStore(SecureCredentialStore):
    """Deterministic in-memory credential store (INTERFACE/SIMULATION only)."""

    kind = "memory"

    def __init__(self) -> None:
        self._tokens: dict[str, str] = {}

    def save_token(self, name: str, token: str) -> None:
        if not token:
            raise ValueError("refusing to store an empty token")
        self._tokens[name] = token

    def read_token(self, name: str) -> str | None:
        return self._tokens.get(name)

    def delete_token(self, name: str) -> bool:
        return self._tokens.pop(name, None) is not None


__all__ = ["InMemorySecureCredentialStore", "SecureCredentialStore"]