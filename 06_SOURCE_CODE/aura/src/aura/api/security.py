"""API security middleware: API key lifecycle, rate limiting, request limits.

This module exists to harden the HTTP API boundary without touching the
canonical domain engines:

- :class:`ApiKeyIssuer` — issue, expire, revoke, and validate opaque API keys.
  Each key is stored as an HMAC digest so a database/leak never reveals the raw
  key.
- :class:`RateLimiter` — fixed-window token bucket per client, with configurable
  burst and refill; exceeding the limit returns 429.
- request size limits and default timeouts are constants the server enforces.

Everything is keyed off the server config and uses the canonical AuditLog, so
security decisions remain auditable.
"""

from __future__ import annotations

import hashlib
import hmac
import threading
import time
from dataclasses import dataclass

from aura.security.audit import AuditLog


@dataclass(frozen=True, slots=True)
class KeySpec:
    """Parameters for one issued API key."""

    key_id: str
    digest: str
    issued_at: float
    expires_at: float | None
    revoked: bool = False
    scopes: tuple[str, ...] = ("*",)

    def to_public_dict(self) -> dict[str, object]:
        return {
            "key_id": self.key_id,
            "issued_at": self.issued_at,
            "expires_at": self.expires_at,
            "revoked": self.revoked,
            "scopes": list(self.scopes),
        }


class ApiKeyIssuer:
    """Issue/expire/revoke/validate API keys with HMAC-digest storage."""

    def __init__(self, *, secret: str, audit: AuditLog | None = None) -> None:
        if not secret or len(secret) < 16:
            raise ValueError("issuer secret must be at least 16 characters")
        self._secret = secret
        self._keys: dict[str, KeySpec] = {}
        self._lock = threading.RLock()
        self._audit = audit or AuditLog()

    def issue(self, *, ttl_seconds: float | None = None, scopes: tuple[str, ...] = ("*",)) -> tuple[str, str]:
        """Return ``(raw_key, key_id)``. The raw key is shown exactly once."""
        import uuid

        key_id = f"kid-{uuid.uuid4().hex[:12]}"
        raw_key = uuid.uuid4().hex + uuid.uuid4().hex
        digest = self._digest(raw_key)
        now = time.time()
        spec = KeySpec(
            key_id=key_id,
            digest=digest,
            issued_at=now,
            expires_at=(now + ttl_seconds) if ttl_seconds is not None else None,
            scopes=scopes,
        )
        with self._lock:
            self._keys[key_id] = spec
        self._audit.record(
            action="api_key.issue",
            actor="system",
            resource=key_id,
            decision="allow",
            reason="key issued",
            payload={"scopes": list(scopes), "ttl_seconds": ttl_seconds},
        )
        return raw_key, key_id

    def validate(self, raw_key: str) -> KeySpec | None:
        """Return the spec when the key is valid (exists, not expired/revoked)."""
        if not raw_key:
            return None
        digest = self._digest(raw_key)
        with self._lock:
            spec = next((s for s in self._keys.values() if hmac.compare_digest(s.digest, digest)), None)
            if spec is None:
                return None
            if spec.revoked:
                return None
            if spec.expires_at is not None and time.time() > spec.expires_at:
                return None
            return spec

    def revoke(self, key_id: str) -> bool:
        with self._lock:
            spec = self._keys.get(key_id)
            if spec is None:
                return False
            self._keys[key_id] = KeySpec(
                key_id=spec.key_id,
                digest=spec.digest,
                issued_at=spec.issued_at,
                expires_at=spec.expires_at,
                revoked=True,
                scopes=spec.scopes,
            )
        self._audit.record(
            action="api_key.revoke",
            actor="system",
            resource=key_id,
            decision="deny",
            reason="API key revoked",
        )
        return True

    def prune_expired(self) -> int:
        now = time.time()
        with self._lock:
            expired = [
                key_id
                for key_id, spec in self._keys.items()
                if spec.expires_at is not None and now > spec.expires_at
            ]
            for key_id in expired:
                del self._keys[key_id]
        return len(expired)

    def _digest(self, raw_key: str) -> str:
        return hmac.new(self._secret.encode("utf-8"), raw_key.encode("utf-8"), hashlib.sha256).hexdigest()

    def stats(self) -> dict[str, int]:
        with self._lock:
            return {"active": sum(1 for s in self._keys.values() if not s.revoked), "total": len(self._keys)}


@dataclass
class RateLimitState:
    ip: str
    tokens: float
    window_start: float


class RateLimiter:
    """Fixed-window token bucket: allows `burst` requests, refills `per_second`."""

    def __init__(self, *, burst: int = 60, per_second: float = 1.0, audit: AuditLog | None = None) -> None:
        self._burst = burst
        self._per_second = per_second
        self._states: dict[str, RateLimitState] = {}
        self._lock = threading.RLock()
        self._audit = audit or AuditLog()

    def allow(self, ip: str) -> bool:
        now = time.time()
        with self._lock:
            state = self._states.get(ip)
            if state is None:
                state = RateLimitState(ip=ip, tokens=float(self._burst), window_start=now)
                self._states[ip] = state
            elapsed = now - state.window_start
            refill = elapsed * self._per_second
            if refill >= 1.0:
                state.tokens = min(float(self._burst), state.tokens + refill)
                state.window_start = now
            if state.tokens < 1.0:
                self._audit.record(
                    action="rate_limit.deny",
                    actor=ip,
                    resource="api",
                    decision="deny",
                    reason="rate limit exceeded",
                )
                return False
            state.tokens -= 1.0
            return True

    def reset(self) -> None:
        with self._lock:
            self._states.clear()


# Secure defaults for the API boundary.
MAX_REQUEST_BYTES = 1_048_576  # 1 MiB
DEFAULT_TIMEOUT_SECONDS = 30.0


def check_request_size(content_length: int, *, limit: int = MAX_REQUEST_BYTES) -> bool:
    """Reject oversized request bodies without reading them into memory."""
    return 0 <= content_length <= limit


__all__ = [
    "ApiKeyIssuer",
    "KeySpec",
    "MAX_REQUEST_BYTES",
    "RateLimiter",
    "check_request_size",
]