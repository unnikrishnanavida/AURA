"""SDK middleware: request-id generation, tracing, and secret redaction.

Observability and safety are cross-cutting concerns handled here rather than
inside the client methods: every request is tagged with a request id and trace
id, and any error message that could echo secret material is redacted using the
canonical :class:`SecretRedactor`.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from aura.security.redaction import SecretRedactor

from .models import SdkRequest, SdkResponse


def _new_id(prefix: str = "rq") -> str:
    import uuid

    return f"{prefix}-{uuid.uuid4().hex[:12]}"


@dataclass
class Middleware:
    """Injects request/trace ids and redacts error text on responses."""

    redactor: SecretRedactor = field(default_factory=SecretRedactor)

    def register_secret(self, secret: str) -> None:
        self.redactor.register(secret)

    def prepare(self, request: SdkRequest, *, trace_id: str = "") -> SdkRequest:
        request_id = request.request_id or _new_id("rq")
        return SdkRequest(
            operation=request.operation,
            payload=request.payload,
            request_id=request_id,
            trace_id=trace_id or request.trace_id or _new_id("tr"),
            timeout_seconds=request.timeout_seconds,
        )

    def finalize(self, response: SdkResponse) -> SdkResponse:
        if response.error is not None and self.redactor.redact(response.error.message) != response.error.message:
            # Preserve the typed error but ensure any echoed secret is masked.
            response.error.message = self.redactor.redact(response.error.message)
        return response


__all__ = ["Middleware"]