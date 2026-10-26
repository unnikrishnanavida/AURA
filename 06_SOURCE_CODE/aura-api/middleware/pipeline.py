"""Middleware for aura-api: correlation, auth, authorization, rate limit.

Middleware is framework-agnostic: each component takes a plain ``RequestContext``
and either mutates it or raises an :class:`ApiError`. The reference HTTP
adapter wires these together; any framework can reuse them.
"""

from __future__ import annotations

from dataclasses import dataclass

from aura_api.auth.authenticator import ApiKeyCredential, Authenticator
from aura_api.authorization.authorizer import Authorizer
from aura_api.core.context import Principal, RequestContext
from aura_api.core.errors import RateLimitExceededError
from aura_api.rate_limit.algorithms import RateLimiter


class CorrelationMiddleware:
    """Ensures every request has a correlation ID (from header or generated)."""

    def __call__(self, context: RequestContext, headers: dict[str, str]) -> None:
        if not context.correlation_id:
            context.correlation_id = headers.get("x-correlation-id", "").strip() or _new_correlation_id()


def _new_correlation_id() -> str:
    import uuid

    return f"co-{uuid.uuid4().hex[:16]}"


@dataclass
class AuthMiddleware:
    """Fail-closed authentication: extracts a bearer credential from headers."""

    authenticator: Authenticator

    def __call__(self, context: RequestContext, headers: dict[str, str]) -> None:
        auth_header = headers.get("authorization", "")
        if not auth_header.lower().startswith("bearer "):
            from aura_api.core.errors import AuthenticationError

            raise AuthenticationError("authorization header must use Bearer scheme")
        credential = ApiKeyCredential(auth_header.split(" ", 1)[1].strip())
        principal = self.authenticator.authenticate(credential)
        context.bind_identity(principal)


@dataclass
class AuthorizationMiddleware:
    """Fail-closed authorization for a (resource_type, action) pair."""

    authorizer: Authorizer
    resource_type: str
    action: str

    def __call__(self, context: RequestContext, headers: dict[str, str]) -> None:
        principal = context.principal or Principal(subject="", roles=())
        self.authorizer.authorize(principal, self.resource_type, self.action)


@dataclass
class RateLimitMiddleware:
    """Enforces a per-identity rate limit; raises 429 when exceeded."""

    limiter: RateLimiter
    route: str = "default"

    def __call__(self, context: RequestContext, headers: dict[str, str]) -> None:
        identity = context.principal.subject if context.principal else (context.client_ip or "anonymous")
        if not self.limiter.allow(f"{identity}:{self.route}"):
            raise RateLimitExceededError(f"rate limit exceeded for identity {identity!r}")


def apply_security_headers(headers: dict[str, str]) -> dict[str, str]:
    """Return the set of security headers that should be present on responses."""
    defaults = {
        "x-content-type-options": "nosniff",
        "x-frame-options": "DENY",
        "content-security-policy": "default-src 'none'",
        "cache-control": "no-store",
    }
    # normalize incoming keys to lowercase, then layer on defaults
    normalized = {k.lower(): v for k, v in headers.items()}
    return {**defaults, **{k: v for k, v in normalized.items() if k not in defaults}}


__all__ = [
    "AuthMiddleware",
    "AuthorizationMiddleware",
    "CorrelationMiddleware",
    "RateLimitMiddleware",
    "apply_security_headers",
]