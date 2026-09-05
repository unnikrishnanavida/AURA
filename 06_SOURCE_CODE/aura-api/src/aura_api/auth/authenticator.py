"""Authentication for aura-api.

Authentication MUST fail closed: an invalid, missing, malformed, or revoked
credential never reaches the application logic. The authenticator returns a
:class:`Principal` or raises :class:`AuthenticationError` (401). There is no
"best-effort" authentication path.
"""

from __future__ import annotations

import hashlib
import hmac
from dataclasses import dataclass, field
from typing import Protocol

from aura_api.core.context import Principal
from aura_api.core.errors import AuthenticationError


class Credentials(Protocol):
    """Anything that can present a credential string."""

    def value(self) -> str: ...


@dataclass(frozen=True)
class ApiKeyCredential:
    key: str

    def value(self) -> str:
        return self.key


@dataclass(frozen=True)
class ApiKeyRecord:
    """A stored API key with its hashed secret."""

    key_id: str
    key_hash: str
    subject: str
    roles: tuple[str, ...] = ()
    enabled: bool = True
    attributes: dict[str, object] = field(default_factory=dict)


def hash_secret(secret: str) -> str:
    """Deterministic HMAC-based secret hash (never stores plaintext keys)."""
    return hmac.new(b"aura-api-key-v1", secret.encode("utf-8"), hashlib.sha256).hexdigest()


@dataclass
class ApiKeyStore:
    """In-memory credential store keyed by key_id."""

    records: dict[str, ApiKeyRecord] = field(default_factory=dict)

    def register(self, key_id: str, secret: str, *, subject: str, roles: tuple[str, ...] = ()) -> None:
        self.records[key_id] = ApiKeyRecord(
            key_id=key_id,
            key_hash=hash_secret(secret),
            subject=subject,
            roles=roles,
            enabled=True,
        )

    def get(self, key_id: str) -> ApiKeyRecord | None:
        return self.records.get(key_id)


class Authenticator:
    """Fail-closed authenticator for API keys."""

    def __init__(self, store: ApiKeyStore | None = None) -> None:
        self.store = store or ApiKeyStore()

    def authenticate(self, credential: ApiKeyCredential) -> Principal:
        """Authenticate a credential; raises AuthenticationError on ANY failure."""
        if not credential.key or not credential.value():
            raise AuthenticationError("missing credentials")
        parts = credential.value().split(".", 1)
        if len(parts) != 2:
            raise AuthenticationError("malformed credential")
        key_id, secret = parts
        record = self.store.get(key_id)
        if record is None:
            raise AuthenticationError("unknown credential id")
        if not record.enabled:
            raise AuthenticationError("credential is disabled")
        if not hmac.compare_digest(record.key_hash, hash_secret(secret)):
            raise AuthenticationError("invalid credential secret")
        return Principal(
            subject=record.subject,
            roles=record.roles,
            attributes=dict(record.attributes),
            source="api_key",
        )


def require_authenticated(context_principal: Principal | None) -> Principal:
    """Fail-closed guard used by middleware after authentication."""
    if context_principal is None or not context_principal.is_authenticated:
        raise AuthenticationError("authentication required")
    return context_principal


__all__ = [
    "ApiKeyCredential",
    "ApiKeyRecord",
    "ApiKeyStore",
    "Authenticator",
    "hash_secret",
    "require_authenticated",
]