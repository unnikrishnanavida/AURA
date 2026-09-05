"""Transports for the AURA SDK.

Two transports implement the same contract:

* :class:`LocalTransport` runs operations against an in-process canonical
  :class:`aura.Aura` instance (deterministic local mode, no network).
* :class:`HttpTransport` talks to a canonical :class:`AuraApiServer` over HTTP
  with bearer authentication, timeouts, and bounded retries.

Both return the same structured JSON-shaped payloads, so the client surface is
transport-agnostic. Nothing in either transport fabricates behavior the
underlying runtime does not provide.
"""

from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from abc import ABC, abstractmethod
from typing import Any

from aura.foundation.errors import AuraError
from aura.security.audit import AuditLog

from .authentication import Authenticator, authenticator_for
from .config import SdkConfig, TransportMode
from .errors import (
    ApiError,
    SdkError,
    SdkRetryExhaustedError,
    SdkTimeoutError,
    SdkValidationError,
    TransportError,
)
from .events import EventBus
from .models import SdkRequest, SdkResponse
from .retry import RetryPolicy

# operation -> (method, path template). Path parameters are substituted from
# the request payload before the remaining payload is sent as the body.
_HTTP_ROUTES: dict[str, tuple[str, str]] = {
    "health": ("GET", "/health"),
    "ready": ("GET", "/ready"),
    "metrics": ("GET", "/v1/metrics"),
    "audit": ("GET", "/v1/audit"),
    "replay": ("GET", "/v1/replay/{execution_id}"),
    "provenance": ("GET", "/v1/provenance/{execution_id}"),
    "session_create": ("POST", "/v1/sessions"),
    "session_get": ("GET", "/v1/sessions/{session_id}"),
    "reason": ("POST", "/v1/reason"),
    "remember": ("POST", "/v1/remember"),
    "recall": ("POST", "/v1/recall"),
    "observe": ("POST", "/v1/observe"),
    "retrieve": ("POST", "/v1/retrieve"),
    "research": ("POST", "/v1/research"),
    "plan": ("POST", "/v1/plan"),
    "pipeline": ("POST", "/v1/pipeline"),
}

_PATH_PARAMS = ("execution_id", "session_id")


class Transport(ABC):
    """Contract implemented by both local and HTTP transports."""

    @abstractmethod
    def send(self, request: SdkRequest) -> SdkResponse:
        """Execute one typed request and return a typed response."""

    @abstractmethod
    def supported_operations(self) -> tuple[str, ...]:
        """Operations this transport can execute."""
class LocalTransport(Transport):
    """In-process transport backed by the canonical AURA runtime."""

    def __init__(
        self,
        *,
        aura: Any | None = None,
        pipeline: Any | None = None,
        events: EventBus | None = None,
        seed: int = 0,
    ) -> None:
        from aura.sdk.client import Aura

        self.aura = aura or Aura(seed=seed)
        self.audit = AuditLog()
        self.events = events or EventBus()
        self._pipeline = pipeline
        self._seed = seed

    def supported_operations(self) -> tuple[str, ...]:
        return tuple(_HTTP_ROUTES) + ("pipeline",)

    def send(self, request: SdkRequest) -> SdkResponse:
        started = time.monotonic()
        try:
            payload = self._dispatch(request.operation, request.payload)
            return SdkResponse(
                operation=request.operation,
                ok=True,
                payload=payload,
                request_id=request.request_id,
                trace_id=request.trace_id,
                duration_ms=(time.monotonic() - started) * 1000.0,
            )
        except (SdkError, AuraError) as exc:
            error = _to_sdk_error(exc)
            return SdkResponse(
                operation=request.operation,
                ok=False,
                payload={},
                request_id=request.request_id,
                trace_id=request.trace_id,
                duration_ms=(time.monotonic() - started) * 1000.0,
                error=error,
            )

    def _dispatch(self, operation: str, payload: dict[str, Any]) -> dict[str, Any]:
        if operation == "health":
            return {"status": "ok", "service": "aura-local", **self.aura.health()}
        if operation == "ready":
            health = self.aura.health()
            return {"status": "ready" if health.get("status") == "ok" else "not_ready", "details": health}
        if operation == "metrics":
            return self.aura.metrics()
        if operation == "audit":
            return {"entries": [r.to_dict() for r in self.audit.entries()]}
        if operation == "reason":
            question = payload.get("question")
            if not isinstance(question, str) or not question.strip():
                raise SdkValidationError("field 'question' is required")
            return self.aura.reason(question, facts=payload.get("facts", {}))
        if operation == "remember":
            return {
                "memory_id": self.aura.remember(
                    key=payload["key"],
                    content=payload["content"],
                    kind=_kind(payload.get("kind", "episodic")),
                    importance=float(payload.get("importance", 0.5)),
                )
            }
        if operation == "recall":
            return {"entries": self.aura.recall(str(payload.get("text", "")), limit=int(payload.get("limit", 10)))}
        if operation == "observe":
            statement = payload.get("statement")
            if not isinstance(statement, str) or not statement.strip():
                raise SdkValidationError("field 'statement' is required")
            predicate = tuple(str(p) for p in (payload.get("predicate") or ()))
            return {"claim_id": self.aura.observe(statement=statement, predicate=predicate)}
        if operation == "retrieve":
            predicate = tuple(str(p) for p in (payload.get("predicate") or ()))
            return {
                "claims": self.aura.retrieve(
                    predicate=predicate,
                    statement=str(payload.get("statement", "")),
                    limit=int(payload.get("limit", 10)),
                )
            }
        if operation == "research":
            return self.aura.research(
                str(payload.get("question", "")),
                claims=tuple(str(c) for c in (payload.get("claims") or ())),
                evidence=payload.get("evidence"),
            )
        if operation == "plan":
            return _plan_from_payload(self.aura, payload)
        if operation == "session_create":
            session_id = f"ses-{int(time.time() * 1000)}"
            return {"session_id": session_id, "created_at": "local"}
        if operation == "pipeline":
            return _pipeline_from_payload(self._pipeline, payload)
        raise SdkValidationError(f"operation {operation!r} not supported by local transport")
class HttpTransport(Transport):
    """HTTP transport against the canonical AURA API server."""

    def __init__(
        self,
        config: SdkConfig,
        *,
        authenticator: Authenticator | None = None,
        retry: RetryPolicy | None = None,
    ) -> None:
        if config.mode is not TransportMode.HTTP:
            raise SdkValidationError("HttpTransport requires mode=TransportMode.HTTP")
        self.config = config
        self.authenticator = authenticator or authenticator_for(config.api_key)
        self.retry = retry or RetryPolicy(config.retry)

    def supported_operations(self) -> tuple[str, ...]:
        return tuple(_HTTP_ROUTES)

    def send(self, request: SdkRequest) -> SdkResponse:
        started = time.monotonic()
        try:
            payload = self._execute(request)
            return SdkResponse(
                operation=request.operation,
                ok=True,
                payload=payload,
                request_id=request.request_id,
                trace_id=request.trace_id,
                duration_ms=(time.monotonic() - started) * 1000.0,
            )
        except SdkError as exc:
            return SdkResponse(
                operation=request.operation,
                ok=False,
                payload={},
                request_id=request.request_id,
                trace_id=request.trace_id,
                duration_ms=(time.monotonic() - started) * 1000.0,
                error=exc,
            )

    def _execute(self, request: SdkRequest) -> dict[str, Any]:
        route = _HTTP_ROUTES.get(request.operation)
        if route is None:
            raise SdkValidationError(f"operation {request.operation!r} not supported over HTTP")
        method, template = route
        url, body = self._build_request(method, template, request.payload)
        deadline = request.timeout_seconds or self.config.timeout_seconds

        def attempt() -> tuple[int, dict[str, Any]]:
            return self._roundtrip(method, url, body, deadline)

        try:
            status, payload = self.retry.run(attempt)  # type: ignore[arg-type]
        except SdkRetryExhaustedError as exc:
            raise exc
        if not 200 <= status < 300:
            code = payload.get("error", {}).get("code") if isinstance(payload, dict) else None
            message = payload.get("error", {}).get("message") if isinstance(payload, dict) else f"http {status}"
            raise ApiError(str(message), http_status=status, api_code=str(code), request_id=request.request_id)
        return payload if isinstance(payload, dict) else {}

    def _build_request(self, method: str, template: str, payload: dict[str, Any]) -> tuple[str, dict[str, Any]]:
        path = template
        remaining = dict(payload)
        for name in _PATH_PARAMS:
            if "{" + name + "}" in path:
                value = remaining.pop(name, None)
                if value is None:
                    raise SdkValidationError(f"path parameter {name!r} is required")
                path = path.replace("{" + name + "}", str(value))
        return self.config.endpoint + path, remaining

    def _roundtrip(self, method: str, url: str, body: dict[str, Any], timeout: float) -> tuple[int, dict[str, Any]]:
        headers = {"Content-Type": "application/json"}
        auth = self.authenticator.authorization_header()
        if auth is not None:
            headers["Authorization"] = auth
        data = json.dumps(body).encode("utf-8") if method == "POST" else None
        req = urllib.request.Request(url, data=data, headers=headers, method=method)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as response:
                raw = response.read()
                status = response.status
        except urllib.error.HTTPError as exc:
            raw = exc.read()
            status = exc.code
        except urllib.error.URLError as exc:
            raise TransportError(f"connection failed: {exc.reason}") from exc
        except TimeoutError as exc:
            raise SdkTimeoutError(f"request timed out after {timeout}s") from exc
        try:
            parsed = json.loads(raw.decode("utf-8")) if raw else {}
        except json.JSONDecodeError as exc:
            raise TransportError("server returned non-JSON response") from exc
        return status, parsed if isinstance(parsed, dict) else {"error": {"code": "api.error", "message": str(parsed)}}  # type: ignore[list-item]
def _kind(name: str) -> Any:
    from aura.memory.models import MemoryType

    try:
        return MemoryType(name)
    except ValueError as exc:
        raise SdkValidationError(f"unknown memory kind {name!r}") from exc


def _to_sdk_error(exc: BaseException) -> SdkError:
    if isinstance(exc, SdkError):
        return exc
    if isinstance(exc, AuraError):
        error = SdkError(exc.message)
        error.code = exc.code  # type: ignore[attr-defined]
        return error
    return SdkError(str(exc))


def _plan_from_payload(aura: Any, payload: dict[str, Any]) -> dict[str, Any]:
    from aura.planning.engine import PlanningEngine
    from aura.planning.models import Goal, Task

    goal_text = payload.get("goal")
    tasks_raw = payload.get("tasks")
    if not isinstance(goal_text, str) or not goal_text.strip():
        raise SdkValidationError("field 'goal' is required")
    if not isinstance(tasks_raw, list):
        raise SdkValidationError("field 'tasks' must be a list")
    tasks: list[Task] = []
    for raw in tasks_raw:
        if not isinstance(raw, dict) or not isinstance(raw.get("name"), str):
            raise SdkValidationError("each task must be an object with a 'name' string")
        tasks.append(
            Task(
                name=raw["name"],
                prerequisites=tuple(str(p) for p in raw.get("prerequisites", ())),
                capability=str(raw.get("capability", "domain.execute")),
                estimated_cost=float(raw.get("estimated_cost", 1.0)),
                risk=float(raw.get("risk", 0.2)),
                rollback_feasible=bool(raw.get("rollback_feasible", True)),
            )
        )
    result = PlanningEngine().plan(goal=Goal.create(description=goal_text), tasks=tasks)
    return {
        "plan_created": result.primary is not None,
        "plan_id": str(result.primary.id) if result.primary else None,
        "steps": result.primary.names if result.primary else [],
        "risk": result.primary.risk.level if result.primary else None,
        "issues": list(result.issues),
    }


def _pipeline_from_payload(pipeline: Any, payload: dict[str, Any]) -> dict[str, Any]:
    from aura.core.pipeline import PipelineRequest
    from aura.planning.models import Goal, Task

    if pipeline is None:
        raise SdkValidationError("pipeline not configured for this client")
    question = payload.get("question")
    goal_text = payload.get("goal")
    if not isinstance(question, str) or not question.strip():
        raise SdkValidationError("field 'question' is required")
    if not isinstance(goal_text, str) or not goal_text.strip():
        raise SdkValidationError("field 'goal' is required")
    tasks: list[Task] = []
    for raw in payload.get("tasks") or []:
        if isinstance(raw, dict) and isinstance(raw.get("name"), str):
            tasks.append(
                Task(
                    name=raw["name"],
                    capability=str(raw.get("capability", "domain.execute")),
                    risk=float(raw.get("risk", 0.1)),
                )
            )
    result = pipeline.run(
        PipelineRequest(
            question=question,
            claims=tuple(str(c) for c in (payload.get("claims") or ())),
            goal=Goal.create(description=goal_text),
            tasks=tuple(tasks),
            action_inputs={
                str(k): dict(v) for k, v in (payload.get("action_inputs") or {}).items() if isinstance(v, dict)
            },
        )
    )
    return result.to_dict()


__all__ = ["HttpTransport", "LocalTransport", "Transport"]