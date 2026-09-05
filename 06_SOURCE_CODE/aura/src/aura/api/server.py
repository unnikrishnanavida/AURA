"""AURA API service.

A dependency-light HTTP API exposing the platform through stable endpoints
using the standard library HTTP server. Every response carries correlation
and execution ids.

Overview of endpoints:

  GET  /health                  liveness
  GET  /ready                   readiness
  GET  /openapi.json            OpenAPI description
  POST /v1/reason               one reasoning pass
  POST /v1/remember             write a memory record
  POST /v1/recall               recall memory records
  POST /v1/observe              add a knowledge claim
  POST /v1/retrieve             retrieve knowledge claims
  POST /v1/research             evidence-aware research cycle
  POST /v1/plan                 create a validated plan
  POST /v1/sessions             open a session
  GET  /v1/sessions/{id}        session info
  GET  /v1/metrics              metrics snapshot
  GET  /v1/audit                audit log entries
  GET  /v1/provenance/{exec}    provenance for an execution
  GET  /v1/replay/{exec}        replay a recorded execution
  POST /v1/pipeline             full canonical request flow (inert actions only)

Security: when ``api_key`` is configured, all ``/v1/*`` endpoints require an
``Authorization: Bearer <key>`` header. The pipeline endpoint executes only the
two registered inert actions (echo/note) and routes every action through the
guardrail gate; it never touches the filesystem, network, or subprocesses.
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import urlparse

from aura.core.pipeline import ExecutionPipeline
from aura.execution.models import ActionResult, ActionSpec, make_result
from aura.foundation.cancellation import CancellationToken
from aura.foundation.errors import AuraError, ConfigurationError
from aura.foundation.ids import CorrelationId
from aura.observability.logging import StructuredLogger
from aura.sdk.client import Aura
from aura.security.audit import AuditLog


class _ApiValidation(Exception):
    """Internal control-flow: a 400 response was already sent."""


_PIPELINE_ACTIONS = {"echo", "note"}


@dataclass
class ServerConfig:
    host: str = "127.0.0.1"
    port: int = 8765
    api_key: str | None = None
    allow_pipeline: bool = False
    pipeline_actions: tuple[str, ...] = ("echo", "note")


OPENAPI: dict[str, Any] = {
    "openapi": "3.0.3",
    "info": {
        "title": "AURA API",
        "version": "0.2.0",
        "description": "Autonomous Universal Reasoning Architecture HTTP API",
    },
    "securitySchemes": {
        "bearerAuth": {"type": "http", "scheme": "bearer"},
    },
    "components": {"securitySchemes": {"bearerAuth": {"type": "http", "scheme": "bearer"}}},
    "paths": {
        "/health": {"get": {"summary": "Liveness", "responses": {"200": {"description": "alive"}}}},
        "/ready": {"get": {"summary": "Readiness", "responses": {"200": {"description": "ready"}}}},
        "/v1/reason": {
            "post": {
                "summary": "Run a reasoning pass",
                "requestBody": {"content": {"application/json": {"schema": {"type": "object"}}}},
                "responses": {"200": {"description": "Reasoning result"}},
                "security": [{"bearerAuth": []}],
            }
        },
        "/v1/remember": {
            "post": {
                "summary": "Write a memory record",
                "requestBody": {"content": {"application/json": {"schema": {"type": "object"}}}},
                "responses": {"200": {"description": "Memory write result"}},
                "security": [{"bearerAuth": []}],
            }
        },
        "/v1/recall": {
            "post": {
                "summary": "Recall memory records",
                "requestBody": {"content": {"application/json": {"schema": {"type": "object"}}}},
                "responses": {"200": {"description": "Recalled memories"}},
                "security": [{"bearerAuth": []}],
            }
        },
        "/v1/research": {
            "post": {
                "summary": "Run an evidence-aware research cycle",
                "requestBody": {"content": {"application/json": {"schema": {"type": "object"}}}},
                "responses": {"200": {"description": "Research output"}},
                "security": [{"bearerAuth": []}],
            }
        },
        "/v1/plan": {
            "post": {
                "summary": "Create a validated plan",
                "requestBody": {"content": {"application/json": {"schema": {"type": "object"}}}},
                "responses": {"200": {"description": "Plan result"}},
                "security": [{"bearerAuth": []}],
            }
        },
        "/v1/replay/{execution_id}": {
            "get": {
                "summary": "Replay an execution",
                "parameters": [
                    {
                        "name": "execution_id",
                        "in": "path",
                        "required": True,
                        "schema": {"type": "string"},
                    }
                ],
                "responses": {"200": {"description": "Recorded trajectory"}},
                "security": [{"bearerAuth": []}],
            }
        },
    },
}
class AuraApiServer:
    """Wraps the stdlib HTTP server with the AURA SDK."""

    def __init__(
        self,
        *,
        aura: Aura | None = None,
        config: ServerConfig | None = None,
        audit_log: AuditLog | None = None,
        aura_config: Any | None = None,
    ) -> None:
        if aura is None:
            aura = Aura(config=aura_config) if aura_config is not None else Aura()
        self.aura = aura
        self.config = config or ServerConfig()
        self.audit = audit_log or AuditLog()
        self.sessions: dict[str, dict[str, object]] = {}
        self.logger = StructuredLogger("aura.api")
        self._pipeline_cache: ExecutionPipeline | None = None

    def _pipeline(self) -> ExecutionPipeline:
        """Lazily build the canonical pipeline with safely inert actions only."""
        from aura.core.pipeline import default_guardrails
        from aura.execution.registry import ActionRegistry

        if self._pipeline_cache is not None:
            return self._pipeline_cache

        registry = ActionRegistry()
        allowed = {name for name in self.config.pipeline_actions if name in _PIPELINE_ACTIONS}

        def echo_action(inputs: Any, token: CancellationToken) -> ActionResult:
            token.check()
            return make_result(ok=True, output={"echo": dict(inputs.values)})

        def note_action(inputs: Any, token: CancellationToken) -> ActionResult:
            token.check()
            return make_result(ok=True, output={"note": str(inputs.get("text", ""))})

        specs = {
            "echo": ("tool.echo", echo_action, 0.0),
            "note": ("tool.note", note_action, 0.05),
        }
        for name in ("echo", "note"):
            if name not in allowed:
                continue
            capability, handler, risk = specs[name]
            registry.register(
                ActionSpec(
                    name=name,
                    capability=capability,
                    handler=handler,
                    risk=risk,
                    expected_effects=(name,),
                    timeout_seconds=10.0,
                    declare_world_changes=False,
                )
            )
        from aura.memory.policy import MemoryLifecycle

        self._pipeline_cache = ExecutionPipeline(
            brain=self.aura.brain,
            registry=registry,
            guardrails=default_guardrails(registry),
            audit=self.audit,
            memory_lifecycle=MemoryLifecycle(engine=self.aura.brain.memory),
        )
        return self._pipeline_cache

    def _create_session(self) -> str:
        """Open a new session and return its id."""
        from aura.foundation.ids import new_hex

        session_id = f"ses-{new_hex()}"
        self.sessions[session_id] = {
            "created_at": self.aura.config.environment.value,
            "events": 0,
        }
        return session_id

    def _handler(self) -> type[BaseHTTPRequestHandler]:
        service = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, fmt: str, *args: Any) -> None:  # noqa: A002
                return

            def _send(self, status: int, payload: dict[str, Any], correlation: CorrelationId) -> None:
                body = json.dumps(payload, sort_keys=True).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("X-Correlation-Id", str(correlation))
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def _error(
                self,
                status: int,
                message: str,
                correlation: CorrelationId,
                code: str = "api.error",
            ) -> None:
                self._send(status, {"error": {"code": code, "message": message}}, correlation)

            def _read_json(self) -> dict[str, Any] | None:
                length = int(self.headers.get("Content-Length", "0") or 0)
                if length <= 0:
                    return {}
                try:
                    data = json.loads(self.rfile.read(length).decode("utf-8"))
                    return data if isinstance(data, dict) else None
                except json.JSONDecodeError:
                    return None

            def _authorized(self, correlation: CorrelationId) -> bool:
                key = service.config.api_key
                if key is None:
                    return True
                expected = f"Bearer {key}"
                return self.headers.get("Authorization", "") == expected

            def _require_auth(self, correlation: CorrelationId) -> bool:
                if not self._authorized(correlation):
                    self._error(401, "authentication required", correlation, "api.auth_failed")
                    return False
                return True

            def _field(self, body: dict[str, Any], name: str, correlation: CorrelationId) -> Any:
                """Return the field value or raise after emitting a 400."""
                if name not in body:
                    self._error(
                        400,
                        f"field {name!r} is required",
                        correlation,
                        "api.validation",
                    )
                    raise _ApiValidation
                return body[name]

            def do_GET(self) -> None:
                correlation = CorrelationId.new()
                path = urlparse(self.path).path
                if path == "/health":
                    self._send(200, {"status": "ok", "service": "aura-api"}, correlation)
                    return
                if path == "/ready":
                    health = service.aura.health()
                    ready = health["status"] == "ok"
                    self._send(
                        200 if ready else 503,
                        {"status": "ready" if ready else "not_ready", "details": health},
                        correlation,
                    )
                    return
                if path.startswith("/v1/replay/"):
                    if not self._require_auth(correlation):
                        return
                    execution_id = path.split("/v1/replay/", 1)[1]
                    try:
                        replay = service.aura.replay(execution_id)
                        self._send(200, replay, correlation)
                    except AuraError as exc:
                        self._error(404, exc.message, correlation, exc.code)
                    return
                if path.startswith("/v1/provenance/"):
                    if not self._require_auth(correlation):
                        return
                    execution_id = path.split("/v1/provenance/", 1)[1]
                    try:
                        self._send(200, service.aura.provenance(execution_id), correlation)
                    except AuraError as exc:
                        self._error(404, exc.message, correlation, exc.code)
                    return
                if path.startswith("/v1/sessions/"):
                    if not self._require_auth(correlation):
                        return
                    session_id = path.split("/v1/sessions/", 1)[1]
                    session = service.sessions.get(session_id)
                    if session is None:
                        self._error(404, f"session not found: {session_id}", correlation, "api.not_found")
                        return
                    self._send(200, {"session_id": session_id, **session}, correlation)
                    return
                if path == "/v1/metrics":
                    if not self._require_auth(correlation):
                        return
                    self._send(200, service.aura.metrics(), correlation)
                    return
                if path == "/v1/audit":
                    if not self._require_auth(correlation):
                        return
                    self._send(
                        200,
                        {"entries": [r.to_dict() for r in service.audit.entries()]},
                        correlation,
                    )
                    return
                if path == "/openapi.json":
                    self._send(200, OPENAPI, correlation)
                    return
                self._error(404, f"unknown endpoint {path}", correlation, "api.not_found")

            def do_POST(self) -> None:
                correlation = CorrelationId.new()
                path = urlparse(self.path).path
                if path not in {
                    "/v1/reason",
                    "/v1/remember",
                    "/v1/recall",
                    "/v1/observe",
                    "/v1/retrieve",
                    "/v1/research",
                    "/v1/plan",
                    "/v1/sessions",
                    "/v1/pipeline",
                }:
                    self._error(404, f"unknown endpoint {path}", correlation, "api.not_found")
                    return
                # Read the body before the auth check so the client is never
                # left mid-send when we respond (prevents connection aborts).
                body = self._read_json()
                if not self._require_auth(correlation):
                    return
                if body is None:
                    self._error(400, "request body must be a JSON object", correlation, "api.invalid_json")
                    return

                if path == "/v1/reason":
                    self._handle_reason(body, correlation)
                    return
                if path == "/v1/remember":
                    self._handle_remember(body, correlation)
                    return
                if path == "/v1/recall":
                    self._handle_recall(body, correlation)
                    return
                if path == "/v1/observe":
                    self._handle_observe(body, correlation)
                    return
                if path == "/v1/retrieve":
                    self._handle_retrieve(body, correlation)
                    return
                if path == "/v1/research":
                    self._handle_research(body, correlation)
                    return
                if path == "/v1/plan":
                    self._handle_plan(body, correlation)
                    return
                if path == "/v1/sessions":
                    service._create_session()
                    session_id = list(service.sessions)[-1]
                    self._send(
                        201,
                        {"session_id": session_id, **service.sessions[session_id]},
                        correlation,
                    )
                    return
                if path == "/v1/pipeline":
                    self._handle_pipeline(body, correlation)
                    return

            def _handle_reason(self, body: dict[str, Any], correlation: CorrelationId) -> None:
                question = body.get("question")
                if not isinstance(question, str) or not question.strip():
                    self._error(400, "field 'question' is required and must be a string", correlation, "api.validation")
                    return
                facts = body.get("facts", {})
                if not isinstance(facts, dict):
                    self._error(400, "field 'facts' must be an object mapping to numbers", correlation, "api.validation")
                    return
                result = service.aura.reason(question, facts=facts)
                self._send(200, result, correlation)

            def _handle_remember(self, body: dict[str, Any], correlation: CorrelationId) -> None:
                from aura.memory.models import MemoryType

                key = body.get("key")
                content = body.get("content")
                if not isinstance(key, str) or not key.strip():
                    self._error(400, "field 'key' is required and must be a string", correlation, "api.validation")
                    return
                if not isinstance(content, dict):
                    self._error(400, "field 'content' must be an object", correlation, "api.validation")
                    return
                kind_name = body.get("kind", "episodic")
                try:
                    kind = MemoryType(kind_name)
                except ValueError:
                    self._error(400, f"unknown memory kind {kind_name!r}", correlation, "api.validation")
                    return
                importance = body.get("importance", 0.5)
                if not isinstance(importance, (int, float)) or not 0.0 <= float(importance) <= 1.0:
                    self._error(400, "field 'importance' must be a number in [0,1]", correlation, "api.validation")
                    return
                memory_id = service.aura.remember(key=key, content=content, kind=kind, importance=float(importance))
                self._send(200, {"memory_id": memory_id}, correlation)

            def _handle_recall(self, body: dict[str, Any], correlation: CorrelationId) -> None:
                text = body.get("text")
                if not isinstance(text, str):
                    self._error(400, "field 'text' must be a string", correlation, "api.validation")
                    return
                limit = body.get("limit", 10)
                if not isinstance(limit, int) or limit < 1:
                    self._error(400, "field 'limit' must be a positive integer", correlation, "api.validation")
                    return
                self._send(200, {"entries": service.aura.recall(text, limit=limit)}, correlation)

            def _handle_observe(self, body: dict[str, Any], correlation: CorrelationId) -> None:
                statement = body.get("statement")
                if not isinstance(statement, str) or not statement.strip():
                    self._error(400, "field 'statement' is required", correlation, "api.validation")
                    return
                predicate = body.get("predicate", ())
                if isinstance(predicate, list):
                    predicate = tuple(str(p) for p in predicate)
                claim_id = service.aura.observe(statement=statement, predicate=tuple(predicate))
                self._send(200, {"claim_id": claim_id}, correlation)

            def _handle_retrieve(self, body: dict[str, Any], correlation: CorrelationId) -> None:
                predicate = body.get("predicate", ())
                if isinstance(predicate, list):
                    predicate = tuple(str(p) for p in predicate)
                statement = body.get("statement", "")
                limit = body.get("limit", 10)
                claims = service.aura.retrieve(
                    predicate=tuple(predicate),
                    statement=statement if isinstance(statement, str) else "",
                    limit=limit if isinstance(limit, int) and limit > 0 else 10,
                )
                self._send(200, {"claims": claims}, correlation)

            def _handle_research(self, body: dict[str, Any], correlation: CorrelationId) -> None:
                question = body.get("question")
                claims = body.get("claims", [])
                if not isinstance(question, str) or not question.strip():
                    self._error(400, "field 'question' is required", correlation, "api.validation")
                    return
                if not isinstance(claims, list):
                    self._error(400, "field 'claims' must be a list of strings", correlation, "api.validation")
                    return
                evidence_raw = body.get("evidence")
                evidence = None
                if isinstance(evidence_raw, dict):
                    evidence = {
                        str(k): (float(v[0]), str(v[1]), float(v[2]))
                        for k, v in evidence_raw.items()
                        if isinstance(v, (list, tuple)) and len(v) == 3
                    }
                output = service.aura.research(question, claims=tuple(str(c) for c in claims), evidence=evidence)
                self._send(200, output, correlation)

            def _handle_plan(self, body: dict[str, Any], correlation: CorrelationId) -> None:
                from aura.planning.engine import PlanningEngine
                from aura.planning.models import Goal, Task

                goal_text = body.get("goal")
                tasks_raw = body.get("tasks")
                if not isinstance(goal_text, str) or not goal_text.strip():
                    self._error(400, "field 'goal' is required and must be a string", correlation, "api.validation")
                    return
                if not isinstance(tasks_raw, list) or not tasks_raw:
                    self._error(400, "field 'tasks' must be a non-empty list", correlation, "api.validation")
                    return
                tasks: list[Task] = []
                for raw in tasks_raw:
                    if not isinstance(raw, dict) or not isinstance(raw.get("name"), str):
                        self._error(400, "each task must be an object with a 'name' string", correlation, "api.validation")
                        return
                    tasks.append(
                        Task(
                            name=raw["name"],
                            prerequisites=tuple(str(p) for p in raw.get("prerequisites", ()) if isinstance(raw.get("prerequisites"), list)),
                            capability=str(raw.get("capability", "domain.execute")),
                            estimated_cost=float(raw.get("estimated_cost", 1.0)),
                            risk=float(raw.get("risk", 0.2)),
                            rollback_feasible=bool(raw.get("rollback_feasible", True)),
                        )
                    )
                result = PlanningEngine().plan(
                    goal=Goal.create(description=goal_text),
                    tasks=tasks,
                )
                self._send(
                    200,
                    {
                        "plan_created": result.primary is not None,
                        "plan_id": str(result.primary.id) if result.primary else None,
                        "steps": result.primary.names if result.primary else [],
                        "risk": result.primary.risk.level if result.primary else None,
                        "issues": list(result.issues),
                    },
                    correlation,
                )

            def _handle_pipeline(self, body: dict[str, Any], correlation: CorrelationId) -> None:
                if not service.config.allow_pipeline:
                    self._error(403, "pipeline endpoint disabled on this server", correlation, "api.disabled")
                    return
                from aura.core.pipeline import PipelineRequest
                from aura.planning.models import Goal, Task

                question = body.get("question")
                goal_text = body.get("goal")
                tasks_raw = body.get("tasks", [])
                if not isinstance(question, str) or not question.strip():
                    self._error(400, "field 'question' is required", correlation, "api.validation")
                    return
                if not isinstance(goal_text, str) or not goal_text.strip():
                    self._error(400, "field 'goal' is required", correlation, "api.validation")
                    return
                tasks: list[Task] = []
                for raw in tasks_raw:
                    if isinstance(raw, dict) and isinstance(raw.get("name"), str):
                        tasks.append(
                            Task(
                                name=raw["name"],
                                capability=str(raw.get("capability", "domain.execute")),
                                risk=float(raw.get("risk", 0.1)),
                            )
                        )
                request = PipelineRequest(
                    question=question,
                    claims=tuple(str(c) for c in body.get("claims", [])),
                    goal=Goal.create(description=goal_text),
                    tasks=tuple(tasks),
                    action_inputs={
                        str(k): dict(v) for k, v in (body.get("action_inputs") or {}).items() if isinstance(v, dict)
                    },
                )
                pipeline = service._pipeline()
                result = pipeline.run(request)
                self._send(200, result.to_dict(), correlation)

        return Handler

    def run(self) -> None:
        server = ThreadingHTTPServer((self.config.host, self.config.port), self._handler())
        self.logger.info("aura-api listening", host=self.config.host, port=str(self.config.port))
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            self.logger.info("aura-api shutting down")
        finally:
            server.server_close()


def run_server(host: str = "127.0.0.1", port: int = 8765) -> None:
    """Run the API server.

    Configuration is loaded from layered sources (env/file); ``AURA_ENVIRONMENT``
    and ``AURA_STORAGE_BACKEND`` are honored. Environment variables that mismatch
    production defaults are validated with the canonical config loader.
    """
    from aura.config.loader import ConfigLoader

    config = ConfigLoader().load()
    # Only bind production-mode enforcement if the environment is explicitly set.
    if os.environ.get("AURA_ENVIRONMENT") == "production" and config.storage.backend == "memory":
        raise ConfigurationError(
            "production run requires storage.backend = 'sqlite' (or 'postgresql'); "
            "refusing to serve with in-memory storage"
        )
    AuraApiServer(
        config=ServerConfig(host=host, port=port),
        aura_config=config,
    ).run()


if __name__ == "__main__":
    run_server(host=sys.argv[1] if len(sys.argv) > 1 else "127.0.0.1")

__all__ = ["AuraApiServer", "OPENAPI", "ServerConfig", "run_server"]