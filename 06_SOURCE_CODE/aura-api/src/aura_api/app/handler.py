"""Reference request processor for aura-api.

This is a framework-agnostic, socket-free handler that demonstrates the full
security pipeline. It is a REFERENCE adapter — NOT a competing production
server. The canonical runtime's production server lives in ``aura.api.server``.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from aura_api.audit.audit_logger import AuditLogger
from aura_api.auth.authenticator import Authenticator
from aura_api.authorization.authorizer import Authorizer
from aura_api.core.context import RequestContext, Tenant
from aura_api.core.errors import (
    ApiError,
    MalformedPayloadError,
    NotFoundError,
)
from aura_api.health.checks import HealthRegistry
from aura_api.middleware.pipeline import (
    AuthMiddleware,
    AuthorizationMiddleware,
    CorrelationMiddleware,
    RateLimitMiddleware,
    apply_security_headers,
)
from aura_api.rate_limit.algorithms import RateLimiter
from aura_api.schemas.responses import ok
from aura_api.schemas.validation import FieldSpec, RequestValidator, non_empty_string
from aura_api.versioning import VersionRegistry

SECURITY_HEADERS = (
    "x-content-type-options",
    "x-frame-options",
    "content-security-policy",
    "cache-control",
)


@dataclass
class ProcessedResponse:
    """The immutable result of processing one request."""

    status: int
    body: dict[str, Any]
    headers: dict[str, str] = field(default_factory=dict)
    correlation_id: str = ""


@dataclass
class ReferenceApi:
    """Wires the middleware + routes into one testable processor."""

    authenticator: Authenticator
    authorizer: Authorizer
    limiter: RateLimiter
    health: HealthRegistry = field(default_factory=HealthRegistry)
    versions: VersionRegistry = field(default_factory=VersionRegistry)
    audit: AuditLogger = field(default_factory=AuditLogger)
    correlation: CorrelationMiddleware = field(default_factory=CorrelationMiddleware)

    def handle(
        self,
        *,
        method: str = "GET",
        path: str = "/",
        headers: dict[str, str] | None = None,
        body: Any = None,
        client_ip: str = "127.0.0.1",
    ) -> ProcessedResponse:
        """Process a single request through the full security pipeline."""
        headers = {k.lower(): v for k, v in (headers or {}).items()}
        context = RequestContext(
            correlation_id="",
            method=method.upper(),
            path=path,
            client_ip=client_ip,
            user_agent=headers.get("user-agent", ""),
        )
        try:
            self.correlation(context, headers)
            response = self._route(context, headers, body)
        except ApiError as exc:
            exc.correlation_id = context.correlation_id
            self.audit.record(
                correlation_id=context.correlation_id,
                event_type="api_error",
                detail=exc.message,
                subject=context.principal.subject if context.principal else None,
                outcome="denied",
            )
            return self._error(context, exc)
        except Exception as exc:  # noqa: BLE001 - fail closed on unexpected error
            self.audit.record(
                correlation_id=context.correlation_id,
                event_type="internal_error",
                detail=f"{type(exc).__name__}: {exc}",
                subject=context.principal.subject if context.principal else None,
                outcome="error",
            )
            internal = ApiError(
                "an internal error occurred",
                code="api.internal",
                status=500,
                correlation_id=context.correlation_id,
            )
            return self._error(context, internal)
        response.headers = apply_security_headers(response.headers)
        return response
    # ------------------------------------------------------------------
    # routing
    # ------------------------------------------------------------------
    def _route(self, context: RequestContext, headers: dict[str, str], body: Any) -> ProcessedResponse:
        path = context.path.split("?", 1)[0]
        if path in ("/health", "/ready"):
            return self._health(context, path)
        version = self.versions.resolve("", from_path=path)
        if path.startswith(f"/{version}/echo") and context.method == "POST":
            return self._echo(context, headers, body)
        raise NotFoundError(f"unknown endpoint {path}")

    def _echo(self, context: RequestContext, headers: dict[str, str], body: Any) -> ProcessedResponse:
        # authentication (fail closed) -> authorization (fail closed) -> rate limit
        AuthMiddleware(self.authenticator)(context, headers)
        AuthorizationMiddleware(self.authorizer, resource_type="echo", action="create")(context, headers)
        RateLimitMiddleware(self.limiter, route="echo")(context, headers)
        context.tenant = Tenant(id="default")

        if isinstance(body, (bytes, bytearray)):
            try:
                body = json.loads(body.decode("utf-8"))
            except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise MalformedPayloadError(f"request body is not valid JSON: {exc}") from exc
        validator = RequestValidator(
            (FieldSpec("message", required=True, kind=str, validators=(non_empty_string,)),),
            allow_extra=False,
        )
        validated = validator.validate(body)
        reply = ok(
            {
                "echo": validated["message"],
                "subject": context.principal.subject if context.principal else None,
            },
            correlation_id=context.correlation_id,
        )
        return ProcessedResponse(
            status=200,
            body=reply,
            correlation_id=context.correlation_id,
        )

    # ------------------------------------------------------------------
    # health / readiness
    # ------------------------------------------------------------------
    def _health(self, context: RequestContext, path: str) -> ProcessedResponse:
        if path == "/health":
            return ProcessedResponse(
                status=200,
                body={"status": "ok", "service": "aura-api"},
                correlation_id=context.correlation_id,
            )
        checks = self.health.run()
        ready = all(c["ok"] for c in checks)
        return ProcessedResponse(
            status=200 if ready else 503,
            body={"status": "ready" if ready else "not_ready", "checks": checks},
            correlation_id=context.correlation_id,
        )

    # ------------------------------------------------------------------
    # error plumbing
    # ------------------------------------------------------------------
    def _error(self, context: RequestContext, exc: ApiError) -> ProcessedResponse:
        exc.correlation_id = context.correlation_id
        return ProcessedResponse(
            status=exc.status,
            body=exc.to_dict(),
            correlation_id=context.correlation_id,
        )


__all__ = ["SECURITY_HEADERS", "ProcessedResponse", "ReferenceApi"]