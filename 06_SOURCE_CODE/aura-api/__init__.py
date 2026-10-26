"""aura-api — reusable API layer for the AURA ecosystem.

This package provides framework-agnostic API functionality: structured
errors, request/response schemas, validation, correlation IDs, fail-closed
authentication and authorization, rate limiting, health/readiness, audit
integration, and API versioning. It also ships a socket-free REFERENCE request
processor (:class:`ReferenceApi`) that demonstrates the full security
pipeline.

The production HTTP server is owned by the canonical runtime
(``aura.api.server``). This package does NOT compete with it.
"""

from __future__ import annotations

from aura_api.app.handler import ProcessedResponse, ReferenceApi
from aura_api.auth.authenticator import ApiKeyStore, Authenticator, hash_secret
from aura_api.authorization.authorizer import ABACPolicy, Authorizer, RBACPolicy
from aura_api.core.context import Principal, RequestContext, Tenant
from aura_api.core.errors import (
    ApiError,
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    InternalError,
    MalformedPayloadError,
    NotFoundError,
    ProblemDetails,
    RateLimitExceededError,
    ValidationError,
    redact,
)
from aura_api.middleware.pipeline import (
    AuthMiddleware,
    AuthorizationMiddleware,
    CorrelationMiddleware,
    RateLimitMiddleware,
    apply_security_headers,
)
from aura_api.rate_limit.algorithms import CompositeLimiter, SlidingWindow, TokenBucket
from aura_api.schemas.responses import ResponseEnvelope, ok, paginated
from aura_api.schemas.validation import (
    FieldSpec,
    RequestValidator,
    bounded,
    non_empty_string,
)
from aura_api.versioning import VersionRegistry

__all__ = [
    "ABACPolicy",
    "ApiError",
    "ApiKeyStore",
    "AuthMiddleware",
    "AuthenticationError",
    "Authenticator",
    "AuthorizationError",
    "AuthorizationMiddleware",
    "Authorizer",
    "CompositeLimiter",
    "ConflictError",
    "CorrelationMiddleware",
    "FieldSpec",
    "InternalError",
    "MalformedPayloadError",
    "NotFoundError",
    "Principal",
    "ProblemDetails",
    "ProcessedResponse",
    "RBACPolicy",
    "RateLimitExceededError",
    "RateLimitMiddleware",
    "ReferenceApi",
    "RequestContext",
    "RequestValidator",
    "ResponseEnvelope",
    "SlidingWindow",
    "Tenant",
    "TokenBucket",
    "ValidationError",
    "VersionRegistry",
    "apply_security_headers",
    "bounded",
    "hash_secret",
    "non_empty_string",
    "ok",
    "paginated",
    "redact",
]