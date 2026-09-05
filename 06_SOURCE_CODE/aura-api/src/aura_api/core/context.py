"""Request context and correlation ID propagation for aura-api.

Every request carries an immutable correlation ID, propagatable through
middleware and logged on every response. The context also carries the
resolved tenant and principal once authentication/authorization succeeds.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


def new_correlation_id() -> str:
    return f"co-{uuid.uuid4().hex[:16]}"


def new_request_id() -> str:
    return f"rq-{uuid.uuid4().hex[:16]}"


@dataclass
class Principal:
    """An authenticated actor."""

    subject: str
    roles: tuple[str, ...] = ()
    attributes: dict[str, Any] = field(default_factory=dict)
    source: str = "api_key"

    @property
    def is_authenticated(self) -> bool:
        return bool(self.subject)


@dataclass(frozen=True)
class Tenant:
    """A tenancy scope for a request."""

    id: str
    name: str = ""


@dataclass
class RequestContext:
    """Immutable-ish context for one request."""

    correlation_id: str
    request_id: str = field(default_factory=new_request_id)
    client_ip: str = "unknown"
    user_agent: str = ""
    path: str = ""
    method: str = ""
    principal: Principal | None = None
    tenant: Tenant | None = None
    started_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def bind_identity(self, principal: Principal | None, tenant: Tenant | None = None) -> None:
        self.principal = principal
        self.tenant = tenant

    def to_log_dict(self) -> dict[str, Any]:
        return {
            "correlation_id": self.correlation_id,
            "request_id": self.request_id,
            "method": self.method,
            "path": self.path,
            "client_ip": self.client_ip,
            "subject": self.principal.subject if self.principal else None,
            "tenant": self.tenant.id if self.tenant else None,
        }


__all__ = [
    "Principal",
    "RequestContext",
    "Tenant",
    "new_correlation_id",
    "new_request_id",
]