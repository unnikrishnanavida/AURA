"""AuraSDK: the stable client facade.

The client owns configuration, authentication, session, event bus, transport,
and middleware, and exposes a typed high-level surface. It is deliberately not
one giant class: state lives in the transport/middleware/session layers, and
this facade only delegates. All failures are typed (see :mod:`aura_sdk.errors`).
"""

from __future__ import annotations

from typing import Any

from .authentication import Authenticator, authenticator_for
from .config import SdkConfig, TransportMode
from .errors import SdkError, SdkValidationError
from .events import EventBus, SdkEvent
from .middleware import Middleware
from .models import SdkRequest, SdkResponse
from .retry import RetryPolicy
from .sessions import Session, SessionManager
from .transport import HttpTransport, LocalTransport, Transport

# Operation names used by the HTTP routes and the local dispatcher.
OPERATIONS = (
    "health",
    "ready",
    "metrics",
    "audit",
    "replay",
    "provenance",
    "session_create",
    "session_get",
    "reason",
    "remember",
    "recall",
    "observe",
    "retrieve",
    "research",
    "plan",
    "pipeline",
)
class AuraSDK:
    """Programmatic client for the AURA platform (local or HTTP)."""

    def __init__(
        self,
        *,
        config: SdkConfig | None = None,
        transport: Transport | None = None,
        authenticator: Authenticator | None = None,
        events: EventBus | None = None,
        middleware: Middleware | None = None,
        seed: int = 0,
        local_pipeline: Any | None = None,
    ) -> None:
        self.config = config or SdkConfig()
        self.events = events or EventBus()
        self.middleware = middleware or Middleware()
        self._sessions = SessionManager()
        self._response_ok = 0
        self._response_failed = 0
        if transport is not None:
            self._transport = transport
        elif self.config.mode is TransportMode.LOCAL:
            self._transport = LocalTransport(seed=seed, pipeline=local_pipeline, events=self.events)
        else:
            self._transport = HttpTransport(
                self.config,
                authenticator=authenticator or authenticator_for(self.config.api_key),
                retry=RetryPolicy(self.config.retry),
            )

    # -- low-level ---------------------------------------------------------
    def start(self) -> str:
        """Initialize the client and return a stable description string."""
        return f"AURA SDK {self.config.mode.value} {self.config.identity}"

    def execute(
        self,
        operation: str,
        payload: dict[str, Any] | None = None,
        *,
        timeout_seconds: float | None = None,
    ) -> SdkResponse:
        """Execute one typed operation through the configured transport."""
        if operation not in OPERATIONS:
            raise SdkValidationError(f"unknown operation {operation!r}")
        request = self.middleware.prepare(
            SdkRequest(operation=operation, payload=payload or {}, timeout_seconds=timeout_seconds)
        )
        self.events.publish(SdkEvent("sdk.request", {"operation": operation}, trace_id=request.trace_id))
        result = self._transport.send(request)
        result = self.middleware.finalize(result)
        if result.ok:
            self._response_ok += 1
        else:
            self._response_failed += 1
        self.events.publish(
            SdkEvent(
                "sdk.response",
                {"operation": operation, "ok": result.ok},
                trace_id=result.trace_id,
            )
        )
        return result

    def request(
        self,
        operation: str,
        payload: dict[str, Any] | None = None,
        *,
        timeout_seconds: float | None = None,
        raise_on_error: bool = True,
    ) -> SdkResponse:
        """Execute an operation and optionally raise on a typed failure."""
        response = self.execute(operation, payload, timeout_seconds=timeout_seconds)
        if raise_on_error and not response.ok:
            if response.error is not None:
                raise response.error
            raise SdkError("operation failed")
        return response
# -- high-level ----------------------------------------------------------
    def health(self) -> dict[str, Any]:
        return self.request("health").payload

    def reason(self, question: str, *, facts: dict[str, float] | None = None) -> dict[str, Any]:
        return self.request("reason", {"question": question, "facts": facts or {}}).payload

    def remember(self, key: str, content: dict[str, Any], *, kind: str = "episodic", importance: float = 0.5) -> str:
        response = self.request(
            "remember", {"key": key, "content": content, "kind": kind, "importance": importance}
        )
        return str(response.payload.get("memory_id"))

    def recall(self, text: str, *, limit: int = 10) -> list[dict[str, Any]]:
        response = self.request("recall", {"text": text, "limit": limit})
        return [dict(e) for e in response.payload.get("entries", [])]

    def observe(self, statement: str, *, predicate: tuple[str, ...] = ()) -> str:
        response = self.request("observe", {"statement": statement, "predicate": list(predicate)})
        return str(response.payload.get("claim_id"))

    def research(self, question: str, *, claims: tuple[str, ...] = ()) -> dict[str, Any]:
        return self.request("research", {"question": question, "claims": list(claims)}).payload

    def metrics(self) -> dict[str, Any]:
        return self.request("metrics").payload

    def session(self) -> Session:
        """Create a new SDK session and return it."""
        response = self.request("session_create", {"identity": self.config.identity})
        session_id = str(response.payload.get("session_id", ""))
        if not session_id:
            raise SdkError("server did not return a session id")
        return self._sessions.create(identity=self.config.identity, metadata={"session_id": session_id})

    @property
    def transport(self) -> Transport:
        return self._transport

    def success_rate(self) -> float:
        """Ratio of successful execute() calls (for telemetry layers)."""
        total = self._response_ok + self._response_failed
        return self._response_ok / total if total else 1.0


__all__ = ["AuraSDK", "OPERATIONS"]