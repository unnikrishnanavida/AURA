"""Structured error types for aura-api.

Invalid requests produce structured Problem+JSON errors. Sensitive
information must never appear in errors, so every error is rendered through
:func:`redact`. All errors carry a stable machine-readable ``code`` and an
HTTP ``status``.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

# Patterns that commonly precede secrets; values following them are masked.
_SECRET_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"(sk-[A-Za-z0-9_-]{6,})", re.IGNORECASE), "<redacted-secret>"),
    (re.compile(r"(api[_-]?key\s*[=:]\s*[A-Za-z0-9_-]{6,})", re.IGNORECASE), "api_key=<redacted>"),
    (re.compile(r"(token\s*[=:]\s*[A-Za-z0-9_.-]{6,})", re.IGNORECASE), "token=<redacted>"),
    (re.compile(r"(bearer\s+[A-Za-z0-9_.-]{6,})", re.IGNORECASE), "bearer <redacted>"),
    (re.compile(r"(password\s*[=:]\s*\S+)", re.IGNORECASE), "password=<redacted>"),
    (re.compile(r"(authorization\s*[=:]\s*\S+)", re.IGNORECASE), "authorization=<redacted>"),
)


def redact(text: str) -> str:
    """Mask secret-like substrings so errors never leak credentials."""
    out = text
    for pattern, replacement in _SECRET_PATTERNS:
        out = pattern.sub(replacement, out)
    return out


class ApiError(Exception):
    """Base class for all aura-api domain errors."""

    code = "api.error"
    status = 500

    def __init__(
        self,
        message: str,
        *,
        code: str | None = None,
        status: int | None = None,
        correlation_id: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        self.message = redact(message)
        self.code = code or self.code
        self.status = status or self.status
        self.correlation_id = correlation_id
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> dict[str, Any]:
        return {
            "error": {
                "code": self.code,
                "message": self.message,
                "correlation_id": self.correlation_id,
                "status": self.status,
                "details": self.details,
            }
        }


class ValidationError(ApiError):
    """A request failed validation; structured 400."""

    code = "api.validation"
    status = 400


class MalformedPayloadError(ApiError):
    """The request body could not be parsed as expected; 400."""

    code = "api.malformed_payload"
    status = 400


class AuthenticationError(ApiError):
    """Authentication failed; must fail closed (401)."""

    code = "api.auth_failed"
    status = 401


class AuthorizationError(ApiError):
    """Authorization failed; must fail closed (403)."""

    code = "api.forbidden"
    status = 403


class RateLimitExceededError(ApiError):
    """The caller exceeded the request-rate budget; 429."""

    code = "api.rate_limited"
    status = 429


class NotFoundError(ApiError):
    """The requested resource does not exist; 404."""

    code = "api.not_found"
    status = 404


class ConflictError(ApiError):
    """The request conflicts with current state; 409."""

    code = "api.conflict"
    status = 409


class InternalError(ApiError):
    """Unexpected internal failure; 500 with redacted details."""

    code = "api.internal"
    status = 500


@dataclass(frozen=True)
class ProblemDetails:
    """RFC-7807-style problem details object."""

    title: str
    status: int
    code: str
    detail: str
    correlation_id: str | None = None
    instance: str | None = None
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "type": "about:blank",
            "title": self.title,
            "status": self.status,
            "code": self.code,
            "detail": redact(self.detail),
        }
        if self.correlation_id:
            payload["correlation_id"] = self.correlation_id
        if self.instance:
            payload["instance"] = self.instance
        payload.update({k: v for k, v in self.extra.items() if not k.startswith("_")})
        return payload


__all__ = [
    "ApiError",
    "AuthenticationError",
    "AuthorizationError",
    "ConflictError",
    "InternalError",
    "MalformedPayloadError",
    "NotFoundError",
    "ProblemDetails",
    "RateLimitExceededError",
    "ValidationError",
    "redact",
]