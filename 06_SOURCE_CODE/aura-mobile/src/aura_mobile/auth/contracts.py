"""Authentication flow contract for aura-mobile.

Defines the auth flow (login -> token -> refresh -> logout) as an explicit
contract. The in-memory implementation is a deterministic double; it never
hardcodes secrets and never stores plaintext tokens (only via the secure
credential store).
"""

from __future__ import annotations

import abc
from dataclasses import dataclass, field
from datetime import UTC, datetime

from aura_mobile.security.secure_store import SecureCredentialStore


@dataclass
class AuthSession:
    """An authenticated session."""

    subject: str
    token_name: str
    authenticated_at: datetime = field(default_factory=lambda: datetime.now(UTC))

    @property
    def active(self) -> bool:
        return bool(self.subject and self.token_name)


class AuthFlowContract(abc.ABC):
    """The auth lifecycle every client must implement."""

    @abc.abstractmethod
    def login(self, username: str, secret: str) -> AuthSession: ...

    @abc.abstractmethod
    def logout(self) -> None: ...

    @abc.abstractmethod
    def current_session(self) -> AuthSession | None: ...


class InMemoryAuthFlow(AuthFlowContract):
    """Deterministic auth double (INTERFACE/SIMULATION)."""

    kind = "memory"

    def __init__(self, store: SecureCredentialStore) -> None:
        self.store = store
        self._session: AuthSession | None = None

    def login(self, username: str, secret: str) -> AuthSession:
        if not username or not secret:
            raise ValueError("username and secret are required")
        # NEVER store the plaintext secret; only a derived token.
        token_name = f"token:{username}"
        self.store.save_token(token_name, f"derived-token-{username}")  # simulation only
        self._session = AuthSession(subject=username, token_name=token_name)
        return self._session

    def logout(self) -> None:
        if self._session is not None:
            self.store.delete_token(self._session.token_name)
            self._session = None

    def current_session(self) -> AuthSession | None:
        return self._session


__all__ = ["AuthFlowContract", "AuthSession", "InMemoryAuthFlow"]