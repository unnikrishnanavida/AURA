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
  GET  /v1/research/runs        list the caller's research runs (owner-scoped,
                                bounded, cursor-paginated)
  POST /v1/plan                 create a validated plan
  POST /v1/sessions             open a session
  GET  /v1/sessions/{id}        session info
  GET  /v1/metrics              metrics snapshot
  GET  /v1/audit                audit log entries
  POST /v1/security/logs        request the security log (support, audited)
  GET  /v1/provenance/{exec}    provenance for an execution
  GET  /v1/replay/{exec}        replay a recorded execution
  POST /v1/pipeline             full canonical request flow (inert actions only)

Security: when ``api_key`` is configured, all ``/v1/*`` endpoints require an
``Authorization: Bearer <key>`` header. The pipeline endpoint executes only the
two registered inert actions (echo/note) and routes every action through the
guardrail gate; it never touches the filesystem, network, or subprocesses.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import threading
import time
from collections import deque
from dataclasses import dataclass, field
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any
from urllib.parse import parse_qs, urlparse

from aura.agents import (
    AgentsBridgeError,
    CanonicalContext,
    agents_available,
    build_agent,
    run_agent_task,
)
from aura.api.authorization import (
    ADMIN_SCOPES,
    ALL_SCOPES,
    STATIC_SCOPES,
    Credential,
    required_scope,
)
from aura.automation import automation_available
from aura.core.pipeline import ExecutionPipeline
from aura.execution.models import ActionResult, ActionSpec, make_result
from aura.foundation.cancellation import CancellationToken, CancellationTokenSource
from aura.foundation.errors import AuraError, CancelledError, ConfigurationError
from aura.foundation.ids import CorrelationId, RequestId
from aura.input.multimodal import MultimodalObservation, ObservationGate, RawAttachment
from aura.observability.logging import StructuredLogger
from aura.research.engine import ResearchEngine
from aura.sdk.client import Aura
from aura.security.audit import AuditLog
from aura.security.capabilities import name_matches


class _ApiValidation(Exception):
    """Internal control-flow: a 400 response was already sent."""


_PIPELINE_ACTIONS = {"echo", "note"}


def _looks_like_request_id(value: Any) -> bool:
    """True for a well-formed request id (``rq-`` prefix optional, hex suffix)."""
    if not isinstance(value, str) or not value:
        return False
    text = value[len("rq-") :] if value.startswith("rq-") else value
    return 1 <= len(text) <= 32 and all(c in "0123456789abcdef" for c in text)


@dataclass
class RequestTask:
    """One cancellable HTTP request registered at the API boundary.

    Owns the canonical :class:`CancellationTokenSource` for the request and
    records status/stage so status and cancel endpoints answer truthfully
    without reaching into engine internals.
    """

    request_id: RequestId
    owner: str
    source: CancellationTokenSource
    status: str = "running"  # running | ok | cancelled | error
    stage: str = "api"
    cancelled_stage: str | None = None
    created_at: float = field(default_factory=time.monotonic)
    finished_at: float | None = None
    result: dict[str, Any] | None = None
    error: str | None = None

    @property
    def token(self) -> CancellationToken:
        return self.source.token

    def to_dict(self) -> dict[str, Any]:
        return {
            "request_id": str(self.request_id),
            "status": self.status,
            "stage": self.stage,
            "cancelled_stage": self.cancelled_stage,
            "created_at": round(self.created_at, 3),
            "finished_at": round(self.finished_at, 3) if self.finished_at is not None else None,
            "result": self.result if self.status == "ok" else None,
            "error": self.error,
        }


class RequestTaskRegistry:
    """Thread-safe registry of in-flight and recently finished HTTP requests.

    The one place that maps a request id to its token and lifecycle state at
    the HTTP boundary (the same layer that already owns sessions, keys and
    rate limits). Completed tasks move to a bounded history so a late status
    or cancel call still observes a deterministic terminal state instead of a
    misleading ``not found``.
    """

    def __init__(self, *, max_history: int = 500) -> None:
        self._active: dict[str, RequestTask] = {}
        self._history: deque[RequestTask] = deque(maxlen=max_history)
        self._lock = threading.RLock()

    def register(self, task: RequestTask) -> None:
        with self._lock:
            self._active[str(task.request_id)] = task

    def get(self, request_id: RequestId) -> RequestTask | None:
        """Live task first, then the bounded terminal history."""
        key = str(request_id)
        with self._lock:
            if key in self._active:
                return self._active[key]
            for task in reversed(self._history):
                if str(task.request_id) == key:
                    return task
            return None

    def finish(
        self,
        task: RequestTask,
        *,
        status: str,
        result: dict[str, Any] | None = None,
        error: str | None = None,
        stage: str | None = None,
    ) -> None:
        """Move a task from active to terminal history (idempotent)."""
        with self._lock:
            if task.status != "running":
                return
            task.status = status
            task.finished_at = time.monotonic()
            task.result = result
            task.error = error
            if stage is not None:
                task.stage = stage
            self._active.pop(str(task.request_id), None)
            self._history.append(task)

    def cancel_active(self, request_id: RequestId) -> bool:
        """Cancel the token of a running request; False when not running."""
        with self._lock:
            task = self._active.get(str(request_id))
            if task is None:
                return False
            task.source.cancel()
            return True

    def cancel_all(self) -> int:
        with self._lock:
            tasks = list(self._active.values())
        for task in tasks:
            task.source.cancel()
        return len(tasks)

    def active_count(self) -> int:
        with self._lock:
            return len(self._active)

    def history_count(self) -> int:
        with self._lock:
            return len(self._history)


@dataclass
class ServerConfig:
    host: str = "127.0.0.1"
    port: int = 8765
    api_key: str | None = None
    api_secret: str | None = None
    admin_key: str | None = None
    trust_proxy: bool = False
    rate_burst: int = 60
    rate_per_second: float = 1.0
    max_request_bytes: int = 1_048_576
    allow_pipeline: bool = False
    pipeline_actions: tuple[str, ...] = ("echo", "note")
    # -- distributed (shared) state for multi-instance deployments ---------
    # When ``distributed_state_dsn`` is set, sessions / API keys / rate limits
    # live in the shared PostgreSQL store so multiple API instances behave as
    # one security boundary. ``distributed_state_policy`` controls degraded
    # behavior when the shared store is unreachable: "fail_closed" (default)
    # denies; "bounded_local" throttles per-instance and is never silent.
    distributed_state_dsn: str | None = None
    distributed_state_policy: str = "fail_closed"
    session_ttl_seconds: float | None = 86400.0
    # -- real alerting (Phase 26) --------------------------------------------
    # When set, the server evaluates metrics/health signals into alerts and
    # posts them to this webhook (or delivers to the structured logger when
    # left empty). Thresholds come from the default rule set and are
    # operator-overridable.
    alert_webhook_url: str | None = None
    alert_instance_id: str = ""


OPENAPI: dict[str, Any] = {
    "openapi": "3.0.3",
    "info": {
        "title": "AURA API",
        "version": "0.2.0",
        "description": "Autonomous Unified Reasoning Architecture HTTP API",
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
                "summary": "Route a chat or reasoning request",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "required": ["question"],
                                "properties": {
                                    "question": {"type": "string", "minLength": 1},
                                    "facts": {
                                        "type": "object",
                                        "additionalProperties": {"type": "number"},
                                    },
                                    "history": {
                                        "type": "array",
                                        "maxItems": 20,
                                        "items": {
                                            "type": "object",
                                            "required": ["role", "content"],
                                            "properties": {
                                                "role": {"type": "string", "enum": ["user", "assistant"]},
                                                "content": {"type": "string", "maxLength": 4000},
                                            },
                                        },
                                    },
                                },
                            }
                        }
                    },
                },
                "responses": {
                    "200": {"description": "Conversation, reasoning, or provider-generation result"},
                    "400": {"description": "Invalid question, facts, or conversation history"},
                },
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
        "/v1/research/runs": {
            "get": {
                "summary": "List the caller's research runs",
                "description": "Owner-scoped, bounded (limit 1..50, default 20), "
                "cursor-paginated by recorder sequence.",
                "parameters": [
                    {
                        "name": "limit",
                        "in": "query",
                        "required": False,
                        "schema": {"type": "integer", "minimum": 1, "maximum": 50, "default": 20},
                    },
                    {
                        "name": "cursor",
                        "in": "query",
                        "required": False,
                        "schema": {"type": "integer", "minimum": 1},
                    },
                ],
                "responses": {
                    "200": {
                        "description": "Page of research runs",
                        "content": {
                            "application/json": {
                                "schema": {
                                    "type": "object",
                                    "properties": {
                                        "runs": {
                                            "type": "array",
                                            "items": {
                                                "type": "object",
                                                "properties": {
                                                    "run_id": {"type": "string"},
                                                    "status": {"type": "string"},
                                                    "question": {"type": "string"},
                                                    "findings_count": {"type": "integer"},
                                                    "epistemic": {"type": "string"},
                                                    "started_at": {"type": "string"},
                                                },
                                            },
                                        },
                                        "next_cursor": {"type": ["integer", "null"]},
                                        "count": {"type": "integer"},
                                        "limit": {"type": "integer"},
                                    },
                                }
                            }
                        },
                    },
                    "400": {"description": "Invalid or out-of-range limit/cursor"},
                    "401": {"description": "Authentication required"},
                },
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
        "/v1/tasks/{id}": {
            "get": {
                "summary": "Status of one request (owner-scoped)",
                "responses": {
                    "200": {"description": "task status"},
                    "403": {"description": "not the request owner"},
                    "404": {"description": "unknown request id"},
                },
                "security": [{"bearerAuth": []}],
            }
        },
        "/v1/tasks/{id}/cancel": {
            "post": {
                "summary": "Cancel one running request (owner-scoped)",
                "responses": {
                    "202": {"description": "cancelling"},
                    "403": {"description": "not the request owner"},
                    "404": {"description": "unknown request id"},
                    "409": {"description": "request already finished"},
                },
                "security": [{"bearerAuth": []}],
            }
        },
        "/v1/agents/run": {
            "post": {
                "summary": "Run one goal through the guarded agent runtime (owner-scoped)",
                "requestBody": {
                    "required": True,
                    "content": {
                        "application/json": {
                            "schema": {
                                "type": "object",
                                "required": ["goal"],
                                "properties": {"goal": {"type": "string"}},
                            }
                        }
                    },
                },
                "responses": {
                    "200": {"description": "agent task outcome"},
                    "403": {"description": "missing agents.run scope"},
                    "503": {"description": "agents runtime not installed"},
                },
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
        # Phase 2A: optional durable state directory. When AURA_DATA_DIR is set,
        # memory and automation tasks persist across restarts; when unset the
        # original in-memory local-first behaviour is preserved exactly.
        _state_dir = os.environ.get("AURA_DATA_DIR")
        _data_config: Any = None
        if _state_dir:
            try:
                from aura.config.settings import AuraConfig, StorageConfig

                _data_config = AuraConfig(
                    storage=StorageConfig(
                        backend="sqlite",
                        sqlite_path=os.path.join(_state_dir, "memory.sqlite3"),
                        knowledge_sqlite_path=os.path.join(_state_dir, "knowledge.sqlite3"),
                    )
                )
            except Exception:  # noqa: BLE001 - an unusable durable config must not block startup
                _data_config = None
        if aura is None:
            aura = Aura(config=aura_config) if aura_config is not None else (Aura(config=_data_config) if _data_config else Aura())
        self.aura = aura
        self.config = config or ServerConfig()
        self.audit = audit_log or AuditLog()
        self.sessions: dict[str, dict[str, object]] = {}
        self.logger = StructuredLogger("aura.api")
        self._pipeline_cache: ExecutionPipeline | None = None
        # One registry mapping request ids to their cancellation token and
        # lifecycle state at the HTTP boundary (Slice 1D).
        self._tasks = RequestTaskRegistry()

        # Phase 1K: canonical automation for bounded long-running tasks. Uses an
        # injected runner that executes each step through the canonical agent
        # bridge (build_agent + run_agent_task); lifecycle/budget/retry/cancel
        # are handled by aura.automation composing the existing runtime.
        self._automation = None
        if automation_available():
            from aura.automation import AutomationManager

            self._automation = AutomationManager(
                runner=self._run_automation_step,
                state_path=(
                    os.path.join(_state_dir, "automation.sqlite3") if _state_dir else None
                ),
            )

        # -- real alerting (Phase 26) --------------------------------------
        from aura.observability.alerts import AlertManager, WebhookAlertChannel, default_rules

        alert_channels: list[object] = []
        if self.config.alert_webhook_url:
            alert_channels.append(WebhookAlertChannel(url=self.config.alert_webhook_url))
        self._alert_manager = AlertManager(
            channels=alert_channels,  # type: ignore[arg-type]
            instance_id=self.config.alert_instance_id or self.config.host or "default",
        )
        for rule in default_rules():
            self._alert_manager.add_rule(rule)

        # -- security middleware -------------------------------------------
        from aura.api.security import ApiKeyIssuer, RateLimiter

        # Duck-typed: `ApiKeyIssuer` and `PostgreSQLApiKeyStore` share the same
        # issue/validate/revoke API. No union type needed; callers stay agnostic.
        self._key_issuer: Any = None
        self._distributed_state: Any = None
        self._session_store: Any = None
        # Duck-typed: both the local and distributed limiters expose
        # `allow(ip: str) -> bool`. The protocol is identical, so no union type
        # is needed and callers stay backend-agnostic.
        self._rate_limiter: Any
        issuer_secret = self.config.api_secret or os.environ.get("AURA_API_SECRET", "")

        if self.config.distributed_state_dsn:
            from aura.api.distributed import (
                DistributedRateLimiter,
                PostgreSQLApiKeyStore,
                PostgreSQLAuditLog,
                PostgreSQLSessionStore,
                PostgreSQLStateStore,
            )

            self._distributed_state = PostgreSQLStateStore(dsn=self.config.distributed_state_dsn)
            self._session_store = PostgreSQLSessionStore(self._distributed_state)
            # A shared flight recorder makes execution replay available on any
            # API instance (multi-instance replay).
            from aura.observability.flight_recorder import PostgreSQLFlightRecorder

            self.aura.brain.recorder = PostgreSQLFlightRecorder(
                self._distributed_state, clock=self.aura._clock
            )
            # A shared audit log lets every instance see the complete
            # security-relevant history.
            self.audit = PostgreSQLAuditLog(self._distributed_state, clock=self.aura._clock)
            self._rate_limiter = DistributedRateLimiter(
                state=self._distributed_state,
                burst=self.config.rate_burst,
                per_second=self.config.rate_per_second,
                degraded_policy=self.config.distributed_state_policy,
                audit=self.audit,
            )
            if self.config.api_key is not None or issuer_secret:
                self._key_issuer = PostgreSQLApiKeyStore(
                    self._distributed_state,
                    secret=issuer_secret or ("dev-secret-not-for-prod-" + (self.config.api_key or "x")),
                    audit=self.audit,
                )
            else:
                self._key_issuer = None
        else:
            if self.config.api_key is not None or issuer_secret:
                self._key_issuer = ApiKeyIssuer(
                    secret=issuer_secret or ("dev-secret-not-for-prod-" + (self.config.api_key or "x")),
                    audit=self.audit,
                )
            else:
                self._key_issuer = None
            self._rate_limiter = RateLimiter(
                burst=self.config.rate_burst,
                per_second=self.config.rate_per_second,
                audit=self.audit,
            )

    def _run_automation_step(
        self,
        step: Any,
        task: Any,
    ) -> Any:
        """Runner used by the automation manager: execute one automation step
        through the canonical guarded agent bridge (build_agent + run_agent_task).

        Capabilities for automation steps are the server-side inert actions
        only -- the client never supplies a capability. A resolved agent refusal
        or task failure is treated as permanent (not auto-retried) because we
        cannot prove it is transient; the owner may retry explicitly. The task's
        cancellation token is threaded through so cancel reaches the active step.
        """
        from aura.agents import CanonicalContext, build_agent, run_agent_task
        from aura.automation import StepOutcome
        from aura.foundation.errors import CancelledError
        from aura.research.engine import ResearchEngine

        if task.token.cancelled:
            return StepOutcome(success=False, cancelled=True)
        try:
            pipeline = self._pipeline()
            agent = build_agent(
                name=f"aura-auto-{task.task_id[-8:]}",
                allow_rules=tuple(step.allow_rules),
                canonical=CanonicalContext(
                    brain=self.aura.brain,
                    memory=self.aura.brain.memory,
                    planning=pipeline.planning,
                    action_registry=pipeline.registry,
                    execution=pipeline.execution,
                ),
            )
            caps = tuple(step.capabilities) or ("actions.echo",)
            criteria = tuple(step.success_criteria) or ("completed == True",)
            outcome = run_agent_task(
                agent=agent,
                description=step.goal,
                success_criteria=criteria,
                capabilities=caps,
                cancellation=task.token,
                research=ResearchEngine(),
                research_claims=tuple(step.research_claims),
                require_research=bool(step.require_research),
            )
        except CancelledError:
            return StepOutcome(success=False, cancelled=True)
        except Exception as exc:  # noqa: BLE001 - classify, never crash
            return StepOutcome(
                success=False,
                failure_class="permanent",
                error=f"automation step failed: {type(exc).__name__}: {exc}",
            )

        if outcome.cancelled:
            return StepOutcome(success=False, cancelled=True)
        if outcome.success:
            return StepOutcome(
                success=True,
                result={
                    "agent_id": outcome.agent_id,
                    "goal_id": outcome.goal_id,
                    "iterations": outcome.iterations,
                    "final_message": outcome.final_message,
                    "evaluation": outcome.evaluation,
                },
            )
        return StepOutcome(
            success=False,
            failure_class="permanent",
            error=outcome.reason or "agent goal failed",
        )

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
        if self._session_store is not None:
            self._session_store.create(
                session_id,
                ttl_seconds=self.config.session_ttl_seconds,
                data={"created_at": self.aura.config.environment.value},
            )
            return session_id
        self.sessions[session_id] = {
            "created_at": self.aura.config.environment.value,
            "events": 0,
        }
        return session_id

    def _dependency_health(self) -> dict[str, object]:
        """Verify the persistence dependency actually works (not just process-alive).

        Runs a real round-trip against the configured memory store so a dead
        database surfaces as unhealthy instead of a false "healthy".
        """
        store = self.aura.brain.memory.store
        backend = type(store).__name__
        try:
            count = store.count()  # forces a real query against the backend
            return {"ok": True, "backend": backend, "entries": count}
        except Exception as exc:  # noqa: BLE001 - surface dependency failure
            return {"ok": False, "backend": backend, "error": str(exc)}

    def _evaluate_alerts(self, health: dict[str, object]) -> list[dict[str, object]]:
        """Evaluate alert rules against the current metrics + health snapshot.

        Delivers alerts to the configured channel(s). Failure to evaluate must
        never break the request path.
        """
        try:
            snapshot = self.aura.metrics()
        except Exception:  # noqa: BLE001 - metrics must never break evaluation
            snapshot = {}
        try:
            fired = self._alert_manager.evaluate(snapshot=snapshot or {}, health=health)
        except Exception:  # noqa: BLE001
            self.logger.error("alert evaluation failed")
            return []
        return [a.to_dict() for a in fired]

    def _handler(self) -> type[BaseHTTPRequestHandler]:
        service = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, fmt: str, *args: Any) -> None:  # noqa: A002
                return

            def _send(self, status: int, payload: dict[str, Any], correlation: CorrelationId) -> None:
                body = json.dumps(payload, sort_keys=True).encode("utf-8")
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
                self.send_header("Access-Control-Allow-Methods", "GET, POST, PATCH, DELETE, OPTIONS")
                self.send_header("Access-Control-Max-Age", "86400")
                self.send_header("X-Correlation-Id", str(correlation))
                self.send_header("Content-Length", str(len(body)))
                # Security headers: harden the HTTP boundary regardless of TLS
                # terminator (the reverse proxy is responsible for HTTPS).
                self.send_header("X-Content-Type-Options", "nosniff")
                self.send_header("X-Frame-Options", "DENY")
                self.send_header("Referrer-Policy", "no-referrer")
                self.send_header("X-Request-Id", str(correlation))
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
                if length > service.config.max_request_bytes:
                    # respond 413 before reading the body (abuse prevention)
                    self._error(413, "request body too large", CorrelationId.new(), "api.too_large")
                    raise _ApiValidation
                try:
                    data = json.loads(self.rfile.read(length).decode("utf-8"))
                    return data if isinstance(data, dict) else None
                except json.JSONDecodeError:
                    return None

            def _credential(self) -> Credential | None:
                """Resolve the presented credential, or ``None`` if there is none.

                Returns a :class:`Credential` (identity + scopes) instead of a
                bare boolean, because "who are you" and "what may you do" are
                different questions. ``None`` means either that no credential
                was presented, or that the one presented is not valid.
                """
                presented = self.headers.get("Authorization", "")
                token = presented.removeprefix("Bearer ").strip()
                key = service.config.api_key

                # The admin key is a bootstrap credential: it may issue and
                # revoke keys, so it carries full scope by construction.
                if service.config.admin_key is not None and token == service.config.admin_key:
                    return Credential(
                        kind="admin",
                        subject="admin",
                        scopes=ADMIN_SCOPES,
                        owner=self._owner_scope(),
                    )
                if key is not None and token == key:
                    return Credential(
                        kind="static",
                        subject="static",
                        scopes=STATIC_SCOPES,
                        owner=self._owner_scope(),
                    )
                if service._key_issuer is not None:
                    spec = service._key_issuer.validate(token)
                    if spec is not None:
                        return Credential(
                            kind="issued",
                            subject=spec.key_id,
                            scopes=tuple(spec.scopes),
                            owner=self._owner_scope(),
                        )
                return None

            def _authorized(self, correlation: CorrelationId) -> bool:
                credential = self._credential()
                if credential is not None:
                    return True
                return bool(
                    service.config.api_key is None and service._key_issuer is None
                )

            def _granted_scopes(self) -> tuple[str, ...]:
                """Scopes held by the current caller.

                In local-first mode (no credential system configured) there are
                no identities to restrict, so the implicit grant is full.
                """
                credential = self._credential()
                return credential.scopes if credential is not None else ("*",)

            def _provider_authorized(self) -> bool:
                """Whether this caller may cause a language model to be consulted.

                Provider use is a separate capability from reasoning: an operator
                can allow AURA to answer from memory while refusing to send
                anything to a model. Checked here so the provider boundary can
                never be reached by a request that lacks the authority.
                """
                return any(
                    name_matches(pattern, "providers.use")
                    for pattern in self._granted_scopes()
                )

            def _owner_scope(self) -> str:
                """Stable owner identity derived from the presented credential.

                One-way digest only (never stores the raw token). Requests with
                no credential map to the anonymous owner, mirroring the notes
                convention. Research runs are attributed to this scope so list
                endpoints can enforce owner isolation server-side.
                """
                presented = self.headers.get("Authorization", "")
                token = presented.removeprefix("Bearer ").strip()
                if not token:
                    return "owner:anonymous"
                digest = hashlib.sha256(token.encode("utf-8")).hexdigest()[:16]
                return f"owner:{digest}"

            def _scoped_owner_scope(self, requested_scope: str | None = None) -> str:
                """Bind caller-selected workspace scopes to the authenticated owner."""
                owner = self._owner_scope()
                if owner == "owner:anonymous":
                    return requested_scope or owner
                if not requested_scope or requested_scope == owner:
                    return owner
                return f"{owner}/{requested_scope}"

            def _check_rate_limit(self, correlation: CorrelationId, proxied: bool = True) -> bool:
                ip = self._client_ip(proxied)
                if not service._rate_limiter.allow(ip):
                    service.aura.brain.metrics.increment("rate_limit_deny")
                    self._error(429, "rate limit exceeded", correlation, "api.rate_limited")
                    return False
                return True

            def _client_ip(self, proxied: bool = True) -> str:
                """Source IP with optional trusted-proxy support.

                ``X-Forwarded-For`` is honored only when the server is configured
                with ``trust_proxy=True`` so a direct connection cannot spoof its
                rate-limit bucket. Defaults to the socket peer address.
                """
                peer = self.client_address[0] if self.client_address else "unknown"
                if not (proxied and service.config.trust_proxy):
                    return peer
                forwarded = self.headers.get("X-Forwarded-For", "")
                if forwarded:
                    return forwarded.split(",")[0].strip() or peer
                return peer

            def _require_auth(self, correlation: CorrelationId) -> bool:
                """Authenticate *and* authorize the current request.

                The required scope is looked up centrally from
                :data:`~aura.api.authorization.ROUTE_SCOPES` so no individual
                route can forget to ask for one. Three distinct outcomes, never
                collapsed into one "connection failed":

                - **allow**: no security boundary configured (local-first
                  single-user mode), or the credential holds the required scope.
                - **401** ``api.auth_failed``: a boundary exists but no valid
                  credential was presented.
                - **403** ``api.forbidden``: the caller is authenticated but the
                  credential lacks the required scope.
                """
                credential = self._credential()
                if credential is None:
                    boundary_configured = (
                        service.config.api_key is not None or service._key_issuer is not None
                    )
                    if not boundary_configured:
                        return True  # local-first mode: no identities to enforce
                    service.aura.brain.metrics.increment("api_auth_failure")
                    self._error(
                        401,
                        "authentication required",
                        correlation,
                        "api.auth_failed",
                    )
                    return False

                required = required_scope(self.command, urlparse(self.path).path)
                if required is None or credential.allows(required):
                    return True

                service.aura.brain.metrics.increment("api_authz_failure")
                service.audit.record(
                    action="api.authz.denied",
                    actor=credential.subject,
                    resource=urlparse(self.path).path,
                    decision="deny",
                    reason=f"missing required scope {required!r}",
                    payload={
                        "required_scope": required,
                        "granted_scopes": list(credential.scopes),
                        "credential_kind": credential.kind,
                    },
                )
                self._error(
                    403,
                    f"this credential is not allowed to {required}",
                    correlation,
                    "api.forbidden",
                )
                return False

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
                if path == "/liveness":
                    # Process alive; does not touch dependencies.
                    self._send(200, {"status": "alive", "service": "aura-api"}, correlation)
                    return
                if path == "/health":
                    # Health discloses engine and dependency internals, so it
                    # verifies the credential whenever a boundary is configured.
                    if not self._require_auth(correlation):
                        return
                    health = service.aura.health()
                    dependency = service._dependency_health()
                    healthy = health.get("status") == "ok" and dependency.get("ok") is True
                    fired = service._evaluate_alerts(
                        {"status": "ok" if healthy else "unhealthy", "dependency": dependency}
                    )
                    self._send(
                        200 if healthy else 503,
                        {"status": "ok" if healthy else "unhealthy",
                         "engines": health.get("engines"),
                         "dependency": dependency,
                         "alerts_fired": fired,
                         "alert_health": service._alert_manager.health()},
                        correlation,
                    )
                    return
                if path == "/ready":
                    # Readiness answers "may this caller use me?", so it must
                    # verify credentials rather than only dependency health.
                    if not self._require_auth(correlation):
                        return
                    health = service.aura.health()
                    dependency = service._dependency_health()
                    ready = health["status"] == "ok" and dependency.get("ok") is True
                    self._send(
                        200 if ready else 503,
                        {"status": "ready" if ready else "not_ready",
                         "details": health,
                         "dependency": dependency},
                        correlation,
                    )
                    return
                if not self._check_rate_limit(correlation):
                    return
                if path == "/v1/automation/tasks":
                    if not self._require_auth(correlation):
                        return
                    self._handle_automation_list(correlation, service)
                    return
                if path.startswith("/v1/automation/tasks/"):
                    if not self._require_auth(correlation):
                        return
                    self._handle_automation_inspect(path, correlation, service)
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
                    if service._session_store is not None:
                        record = service._session_store.get(session_id)
                        if record is None:
                            self._error(404, f"session not found: {session_id}", correlation, "api.not_found")
                            return
                        self._send(
                            200,
                            {"session_id": record.session_id, "created_at": record.created_at, "events": record.events},
                            correlation,
                        )
                        return
                    session = service.sessions.get(session_id)
                    if session is None:
                        self._error(404, f"session not found: {session_id}", correlation, "api.not_found")
                        return
                    self._send(200, {"session_id": session_id, **session}, correlation)
                    return
                if path == "/v1/memory/stats":
                    if not self._require_auth(correlation):
                        return
                    store = service.aura.brain.memory.store
                    self._send(
                        200,
                        {"count": store.count(), "backend": type(store).__name__},
                        correlation,
                    )
                    return
                if path == "/v1/research/runs":
                    if not self._require_auth(correlation):
                        return
                    query = parse_qs(urlparse(self.path).query)
                    limit = 20
                    try:
                        limit = int((query.get("limit") or ["20"])[0])
                    except ValueError:
                        self._error(400, "field 'limit' must be an integer", correlation, "api.validation")
                        return
                    if limit < 1 or limit > 50:
                        self._error(400, "field 'limit' must be between 1 and 50", correlation, "api.validation")
                        return
                    cursor: int | None = None
                    raw_cursor = query.get("cursor")
                    if raw_cursor:
                        try:
                            cursor = int(raw_cursor[0])
                        except ValueError:
                            self._error(400, "field 'cursor' must be an integer sequence", correlation, "api.validation")
                            return
                        if cursor <= 0:
                            self._error(
                                400, "field 'cursor' must be a positive integer", correlation, "api.validation"
                            )
                            return
                    owner = self._owner_scope()
                    events = service.aura.brain.recorder.events(event_type="research.completed")
                    matching = [
                        e for e in events if str(e.payload.get("scope", "owner:anonymous")) == owner
                    ]
                    matching.sort(key=lambda e: (e.sequence, str(e.execution_id)), reverse=True)
                    if cursor is not None:
                        matching = [e for e in matching if e.sequence < cursor]
                    page = matching[:limit]
                    runs = []
                    for event in page:
                        runs.append(
                            {
                                "run_id": str(event.execution_id),
                                "status": "completed",
                                "question": event.payload.get("question", ""),
                                "findings_count": event.payload.get("findings"),
                                "epistemic": event.payload.get("epistemic"),
                                "started_at": event.timestamp,
                            }
                        )
                    next_cursor = page[-1].sequence if len(page) == limit else None
                    self._send(
                        200,
                        {"runs": runs, "next_cursor": next_cursor, "count": len(runs), "limit": limit},
                        correlation,
                    )
                    return
                if path == "/v1/metrics":
                    if not self._require_auth(correlation):
                        return
                    self._send(200, service.aura.metrics(), correlation)
                    return
                if path.startswith("/v1/notes"):
                    if not self._require_auth(correlation):
                        return
                    if path == "/v1/notes":
                        scopes = parse_qs(urlparse(self.path).query).get("scope", [])
                        requested_scope = scopes[0] if scopes else None
                        scope = self._scoped_owner_scope(requested_scope)
                        notes = self._notes(scope)
                        self._send(200, {"notes": notes, "count": len(notes)}, correlation)
                    else:
                        from aura.foundation.ids import MemoryId

                        note_id = path.split("/v1/notes/", 1)[1]
                        try:
                            entry = service.aura.brain.memory.by_id(MemoryId.from_str(note_id))
                        except Exception:  # noqa: BLE001 - 404 for missing notes
                            self._error(404, f"note not found: {note_id}", correlation, "api.not_found")
                            return
                        if not entry.key.startswith("note:"):
                            self._error(404, f"note not found: {note_id}", correlation, "api.not_found")
                            return
                        owner = self._owner_scope()
                        if owner != "owner:anonymous" and not (entry.scope or "").startswith(f"{owner}/"):
                            self._error(404, f"note not found: {note_id}", correlation, "api.not_found")
                            return
                        self._send(
                            200,
                            {"note_id": str(entry.id), "title": entry.content.get("title", ""),
                             "content": entry.content.get("content", ""), "scope": entry.scope},
                            correlation,
                        )
                    return
                if path == "/v1/knowledge/graph":
                    if not self._require_auth(correlation):
                        return
                    limit = 200
                    try:
                        raw = (parse_qs(urlparse(self.path).query).get("limit") or ["200"])[0]
                        limit = max(1, min(int(raw), 500))
                    except ValueError:
                        self._error(400, "field 'limit' must be an integer", correlation, "api.validation")
                        return
                    knowledge = service.aura.brain.knowledge
                    nodes = []
                    for claim in knowledge.claims.values():
                        nodes.append(
                            {
                                "id": str(claim.id),
                                "statement": claim.statement,
                                "predicate": list(claim.predicate),
                                "status": claim.status.value,
                                "confidence": claim.confidence,
                                "contradicts": list(claim.contradicts),
                                "provenance_source": claim.provenance.source,
                            }
                        )
                    # Real persisted relationships: contradiction pairs recorded on claims.
                    edges = []
                    for claim in knowledge.claims.values():
                        for target in claim.contradicts:
                            edges.append({"source": str(claim.id), "target": target, "type": "contradicts"})
                    nodes = nodes[:limit]
                    self._send(
                        200,
                        {
                            "nodes": nodes,
                            "edges": list({f"{e['source']}|{e['target']}|{e['type']}": e for e in edges}.values()),
                            "count": len(nodes),
                        },
                        correlation,
                    )
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
                if path.startswith("/v1/tasks/"):
                    if not self._require_auth(correlation):
                        return
                    self._handle_task_status(path, correlation)
                    return
                if path == "/v1/providers":
                    if not self._require_auth(correlation):
                        return
                    self._send(200, _provider_state_payload(service), correlation)
                    return
                if path == "/openapi.json":
                    self._send(200, OPENAPI, correlation)
                    return
                self._error(404, f"unknown endpoint {path}", correlation, "api.not_found")

            def do_OPTIONS(self) -> None:
                """CORS preflight so the browser web client can reach the API."""
                self.send_response(204)
                self.send_header("Access-Control-Allow-Origin", "*")
                self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
                self.send_header("Access-Control-Allow-Methods", "GET, POST, PATCH, DELETE, OPTIONS")
                self.send_header("Access-Control-Max-Age", "86400")
                self.send_header("Content-Length", "0")
                self.end_headers()

            def do_POST(self) -> None:
                correlation = CorrelationId.new()
                path = urlparse(self.path).path
                if path.startswith("/v1/tasks/"):
                    if path.endswith("/cancel"):
                        # Drain the (empty) body before responding so the
                        # connection closes cleanly instead of an RST.
                        self._read_json()
                        self._handle_cancel_task(path, correlation)
                        return
                    self._error(404, f"unknown endpoint {path}", correlation, "api.not_found")
                    return
                if path == "/v1/automation/tasks":
                    create_body = self._read_json() or {}
                    if not self._require_auth(correlation):
                        return
                    self._handle_automation_create(create_body, correlation, service)
                    return
                if path.startswith("/v1/automation/tasks/"):
                    self._read_json()
                    if not self._require_auth(correlation):
                        return
                    self._handle_automation_action(path, correlation, service)
                    return
                if path == "/v1/keys":
                    self._handle_issue_key(self._read_json() or {}, correlation)
                    return
                if path == "/v1/keys/revoke":
                    self._handle_revoke_key(self._read_json() or {}, correlation)
                    return
                if path not in {
                    "/v1/reason",
                    "/v1/remember",
                    "/v1/recall",
                    "/v1/observe",
                    "/v1/retrieve",
                    "/v1/research",
                    "/v1/plan",
                    "/v1/notes",
                    "/v1/sessions",
                    "/v1/pipeline",
                    "/v1/agents/run",
                    "/v1/security/logs",
                }:
                    self._error(404, f"unknown endpoint {path}", correlation, "api.not_found")
                    return
                # Read the body before the auth check so the client is never
                # left mid-send when we respond (prevents connection aborts).
                body = self._read_json()
                if not self._require_auth(correlation):
                    return
                if not self._check_rate_limit(correlation):
                    return
                if body is None:
                    self._error(400, "request body must be a JSON object", correlation, "api.invalid_json")
                    return

                if path == "/v1/reason":
                    self._handle_reason(body, correlation)
                    return
                if path == "/v1/agents/run":
                    self._handle_agents_run(body, correlation)
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
                    session_id = service._create_session()
                    if service._session_store is not None:
                        record = service._session_store.get(session_id)
                        self._send(
                            201,
                            {"session_id": session_id, "created_at": record.created_at, "events": record.events},
                            correlation,
                        )
                    else:
                        self._send(
                            201,
                            {"session_id": session_id, **service.sessions[session_id]},
                            correlation,
                        )
                    return
                if path == "/v1/notes":
                    self._handle_create_note(body, correlation)
                    return
                if path == "/v1/pipeline":
                    self._handle_pipeline(body, correlation)
                    return
                if path == "/v1/security/logs":
                    self._handle_security_logs(body, correlation)
                    return

            def _handle_security_logs(self, body: dict[str, Any], correlation: CorrelationId) -> None:
                """Explicit user request for the security log (e.g., for support).

                The log is served live from the canonical audit log and the request
                itself is recorded as a security event. Nothing is stored client-side.
                """
                reason = body.get("reason")
                if reason is not None and (not isinstance(reason, str) or len(reason) > 240):
                    self._error(400, "field 'reason' must be a string <= 240 chars", correlation, "api.validation")
                    return
                service.audit.record(
                    action="security.logs.requested",
                    actor="user",
                    resource="security-log",
                    decision="allow",
                    reason=str(reason or "").strip() or "user requested the security log",
                    correlation_id=str(correlation),
                )
                self._send(
                    200,
                    {"entries": [r.to_dict() for r in service.audit.entries()]},
                    correlation,
                )

            def _handle_issue_key(self, body: dict[str, Any], correlation: CorrelationId) -> None:
                if service._key_issuer is None:
                    self._error(404, "key issuance not enabled", correlation, "api.disabled")
                    return
                if not service.config.admin_key or self.headers.get("Authorization") != f"Bearer {service.config.admin_key}":
                    self._error(403, "admin authorization required", correlation, "api.forbidden")
                    return
                requested = tuple(str(s) for s in body.get("scopes", ("*",)))
                # A grant is valid when it is "*", a published scope, or a wildcard pattern
                # that actually covers one (so "memory.*" is accepted while a
                # typo like "memroy.read" is rejected instead of silently
                # minting a key that can never match anything).
                unknown = [
                    s
                    for s in requested
                    if s != "*"
                    and not any(name_matches(s, known) for known in ALL_SCOPES)
                ]
                if unknown:
                    # Reject unknown scopes: a typo would mint a key that can
                    # never match anything, which fails silently and confusingly.
                    self._error(
                        400,
                        f"unknown scope(s): {', '.join(sorted(unknown))}",
                        correlation,
                        "api.validation",
                    )
                    return
                ttl = body.get("ttl_seconds")
                raw_key, key_id = service._key_issuer.issue(
                    ttl_seconds=float(ttl) if isinstance(ttl, (int, float)) else None,
                    scopes=requested,
                )
                self._send(201, {"key_id": key_id, "api_key": raw_key}, correlation)

            def _handle_revoke_key(self, body: dict[str, Any], correlation: CorrelationId) -> None:
                if service._key_issuer is None:
                    self._error(404, "key issuance not enabled", correlation, "api.disabled")
                    return
                if not service.config.admin_key or self.headers.get("Authorization") != f"Bearer {service.config.admin_key}":
                    self._error(403, "admin authorization required", correlation, "api.forbidden")
                    return
                key_id = body.get("key_id")
                if not isinstance(key_id, str) or not key_id:
                    self._error(400, "field 'key_id' is required", correlation, "api.validation")
                    return
                revoked = service._key_issuer.revoke(key_id)
                self._send(200, {"key_id": key_id, "revoked": revoked}, correlation)

            def _handle_reason(self, body: dict[str, Any], correlation: CorrelationId) -> None:
                question = body.get("question")
                if not isinstance(question, str) or not question.strip():
                    self._error(400, "field 'question' is required and must be a string", correlation, "api.validation")
                    return
                facts = body.get("facts", {})
                if not isinstance(facts, dict):
                    self._error(400, "field 'facts' must be an object mapping to numbers", correlation, "api.validation")
                    return
                history = body.get("history", [])
                if not isinstance(history, list) or len(history) > 20:
                    self._error(400, "field 'history' must be a list of at most 20 messages", correlation, "api.validation")
                    return
                validated_history: list[dict[str, str]] = []
                for message in history:
                    if (
                        not isinstance(message, dict)
                        or message.get("role") not in {"user", "assistant"}
                        or not isinstance(message.get("content"), str)
                        or len(message["content"]) > 4000
                    ):
                        self._error(
                            400,
                            "history messages require a user/assistant role and content up to 4000 characters",
                            correlation,
                            "api.validation",
                        )
                        return
                    validated_history.append({"role": message["role"], "content": message["content"]})
                # Optional client-supplied cancellation key: the same id can
                # later be queried (GET /v1/tasks/{id}) or cancelled
                # (POST /v1/tasks/{id}/cancel), always owner-scoped.
                requested_id: Any = body.get("request_id")
                if requested_id is not None and requested_id != "":
                    if not _looks_like_request_id(requested_id):
                        self._error(
                            400,
                            "field 'request_id' must be a hex id (rq- prefix optional)",
                            correlation,
                            "api.validation",
                        )
                        return
                    task_id = RequestId.from_str(requested_id)
                else:
                    task_id = RequestId.new()
                task = RequestTask(
                    request_id=task_id,
                    owner=self._owner_scope(),
                    source=CancellationTokenSource(),
                    stage="api",
                )
                service._tasks.register(task)
                try:
                    result = service.aura.reason(
                        question,
                        facts=facts,
                        history=tuple(validated_history),
                        scope=self._owner_scope(),
                        provider_authorized=self._provider_authorized(),
                        cancellation=task.token,
                    )
                except CancelledError:
                    # The token was already cancelled before any stage ran:
                    # report a clean cancellation rather than an engine failure.
                    task.cancelled_stage = "orchestration"
                    service._tasks.finish(task, status="cancelled", stage="orchestration")
                    self._send(
                        200,
                        {
                            "request_id": str(task_id),
                            "status": "cancelled",
                            "cancelled_stage": "orchestration",
                            "answer": None,
                        },
                        correlation,
                    )
                    return
                except Exception:
                    service._tasks.finish(task, status="error")
                    raise
                # A provider that the caller may not use is an authorization
                # failure, not an answer: surface it as such rather than
                # silently degrading to a bare "I do not know".
                provider_block = result.get("provider")
                if (
                    isinstance(provider_block, dict)
                    and provider_block.get("status") == "unauthorized"
                ):
                    service._tasks.finish(task, status="ok", result=dict(result))
                    self._error(
                        403,
                        "this credential is not allowed to use a language model provider",
                        correlation,
                        "api.provider_forbidden",
                    )
                    return
                if task.token.cancelled:
                    # The client asked to cancel while the request was in
                    # flight. The response reports it in the provider
                    # vocabulary when the provider boundary observed it,
                    # otherwise at the orchestration boundary.
                    cancelled_stage: str | None = (
                        provider_block.get("cancelled_stage")
                        if isinstance(provider_block, dict)
                        and provider_block.get("cancelled_stage")
                        else "orchestration"
                    )
                    task.cancelled_stage = cancelled_stage
                    service._tasks.finish(
                        task, status="cancelled", result=dict(result)
                    )
                    body_out = dict(result)
                    body_out["request_id"] = str(task_id)
                    body_out["status"] = "cancelled"
                    body_out["cancelled_stage"] = cancelled_stage
                    self._send(200, body_out, correlation)
                    return
                service._tasks.finish(task, status="ok", result=dict(result))
                body_out = dict(result)
                body_out["request_id"] = str(task_id)
                body_out["status"] = "ok"
                self._send(200, body_out, correlation)

            def _task_owner_allowed(self, task: RequestTask) -> bool:
                """A caller may only act on their own requests (admin override)."""
                if task.owner == self._owner_scope():
                    return True
                credential = self._credential()
                return credential is not None and credential.kind == "admin"

            def _parse_task_id(self, segment: str) -> RequestId | None:
                """Parse a path/body request id, or None when malformed."""
                if not _looks_like_request_id(segment):
                    return None
                return RequestId.from_str(segment)

            def _handle_task_status(self, path: str, correlation: CorrelationId) -> None:
                segment = path.split("/v1/tasks/", 1)[1]
                task_id = self._parse_task_id(segment)
                if task_id is None:
                    self._error(400, "request_id is invalid", correlation, "api.validation")
                    return
                task = service._tasks.get(task_id)
                if task is None:
                    self._error(404, "unknown request id", correlation, "api.not_found")
                    return
                if not self._task_owner_allowed(task):
                    self._error(403, "not allowed to read this request", correlation, "api.forbidden")
                    return
                self._send(200, task.to_dict(), correlation)

            def _handle_cancel_task(self, path: str, correlation: CorrelationId) -> None:
                if not self._require_auth(correlation):
                    return
                if not self._check_rate_limit(correlation):
                    return
                segment = path[len("/v1/tasks/") : -len("/cancel")]
                task_id = self._parse_task_id(segment)
                if task_id is None:
                    self._error(400, "request_id is invalid", correlation, "api.validation")
                    return
                task = service._tasks.get(task_id)
                if task is None:
                    self._error(404, "unknown request id", correlation, "api.not_found")
                    return
                if not self._task_owner_allowed(task):
                    credential = self._credential()
                    service.audit.record(
                        action="request.cancel_denied",
                        actor=credential.subject if credential is not None else "anonymous",
                        resource=str(task_id),
                        decision="deny",
                        reason="caller does not own this request",
                        correlation_id=str(correlation),
                    )
                    self._error(403, "not allowed to cancel this request", correlation, "api.forbidden")
                    return
                if task.status != "running":
                    self._error(
                        409,
                        f"request is already {task.status}",
                        correlation,
                        "api.conflict",
                    )
                    return
                service._tasks.cancel_active(task_id)
                credential = self._credential()
                service.audit.record(
                    action="request.cancelled",
                    actor=credential.subject if credential is not None else "anonymous",
                    resource=str(task_id),
                    decision="allow",
                    reason="user cancelled their request",
                    correlation_id=str(correlation),
                )
                self._send(
                    202,
                    {"request_id": str(task_id), "status": "cancelling"},
                    correlation,
                )

            def _handle_agents_run(self, body: dict[str, Any], correlation: CorrelationId) -> None:
                """Run one goal through the canonical guarded agent bridge.

                The bridge builds a fresh agent wired to canonical engines:
                reasoning through the canonical BrainEngine (ContextAssembler ->
                memory + knowledge -> ReasoningEngine), planning through the
                canonical PlanningEngine, and execution through the canonical
                guarded actions exposed to the agent (echo/note, both inert).
                No tool is ever injectable from the network. The caller's
                cancellation token is threaded through, and outcomes --
                including capability denials -- are always reported honestly.
                """
                goal = body.get("goal")
                if not isinstance(goal, str) or not goal.strip():
                    self._error(400, "field 'goal' is required and must be a string", correlation, "api.validation")
                    return
                criteria_raw = body.get("success_criteria", [])
                if not isinstance(criteria_raw, list) or not all(isinstance(v, str) for v in criteria_raw):
                    self._error(400, "field 'success_criteria' must be a list of strings", correlation, "api.validation")
                    return
                capabilities_raw = body.get("capabilities", [])
                if not isinstance(capabilities_raw, list) or len(capabilities_raw) > 20 or not all(
                    isinstance(v, str) and v.strip() for v in capabilities_raw
                ):
                    self._error(400, "field 'capabilities' must be a list of at most 20 non-empty strings", correlation, "api.validation")
                    return
                world_raw = body.get("world_state", {})
                if not isinstance(world_raw, dict):
                    self._error(400, "field 'world_state' must be an object", correlation, "api.validation")
                    return

                # Phase 1H: optional canonical research stage for this agent
                # task. Research evaluates *supplied* claims/evidence with the
                # canonical ResearchEngine (deterministic; no external fetch).
                require_research = body.get("require_research", False)
                if not isinstance(require_research, bool):
                    self._error(400, "field 'require_research' must be a boolean", correlation, "api.validation")
                    return
                research_claims_raw = body.get("research_claims", [])
                if not isinstance(research_claims_raw, list) or len(research_claims_raw) > 20 or not all(
                    isinstance(v, str) and v.strip() for v in research_claims_raw
                ):
                    self._error(400, "field 'research_claims' must be a list of at most 20 non-empty strings", correlation, "api.validation")
                    return
                research_evidence_raw = body.get("research_evidence", {})
                if not isinstance(research_evidence_raw, dict):
                    self._error(400, "field 'research_evidence' must be an object", correlation, "api.validation")
                    return
                research_evidence: dict[str, tuple[float, str, float]] = {}
                for claim, value in research_evidence_raw.items():
                    if not isinstance(value, (list, tuple)) or len(value) != 3:
                        self._error(400, "field 'research_evidence' entries must be [strength, source, freshness] triples", correlation, "api.validation")
                        return
                    research_evidence[str(claim)] = (float(value[0]), str(value[1]), float(value[2]))
                research_claims = tuple(str(v) for v in research_claims_raw)

                # Optional cancellation key, identical to /v1/reason (Slice 1D).
                requested_id: Any = body.get("request_id")
                if requested_id is not None and requested_id != "":
                    if not _looks_like_request_id(requested_id):
                        self._error(400, "field 'request_id' must be a hex id (rq- prefix optional)", correlation, "api.validation")
                        return
                    task_id = RequestId.from_str(requested_id)
                else:
                    task_id = RequestId.new()
                task = RequestTask(
                    request_id=task_id,
                    owner=self._owner_scope(),
                    source=CancellationTokenSource(),
                    stage="api",
                )
                service._tasks.register(task)

                # Phase 1J: optional untrusted multimodal observations. Each
                # attachment passes the canonical ObservationGate (cancellation,
                # authorization, size, modality, prompt-injection) and is reported
                # honestly. Only accepted (verified=False) observations reach
                # reasoning; image/audio/video are reported capability_unavailable.
                observations_raw: Any = body.get("observations", [])
                observations_report: list[dict[str, Any]] = []
                accepted_observations: list[MultimodalObservation] = []
                if observations_raw:
                    if not isinstance(observations_raw, list):
                        service._tasks.finish(task, status="error", error="invalid observations")
                        self._error(
                            400,
                            "field 'observations' must be a list",
                            correlation,
                            "api.validation",
                        )
                        return
                    owner_scope = self._owner_scope()
                    gate = ObservationGate()
                    for idx, item in enumerate(observations_raw):
                        if not isinstance(item, dict):
                            observations_report.append(
                                {"index": idx, "status": "malformed", "modality": "unknown", "reason": "observation must be an object"}
                            )
                            continue
                        media_type = item.get("media_type")
                        if not isinstance(media_type, str) or not media_type.strip():
                            observations_report.append(
                                {"index": idx, "status": "malformed", "modality": "unknown", "reason": "field 'media_type' is required and must be a string"}
                            )
                            continue
                        content = item.get("content")
                        extracted = item.get("extracted_text")
                        content = content if isinstance(content, str) else ""
                        extracted = extracted if isinstance(extracted, str) else ""
                        size_raw = item.get("size_bytes")
                        if isinstance(size_raw, int) and size_raw >= 0:
                            size = size_raw
                        else:
                            size = len((content or extracted).encode("utf-8")) if (content or extracted) else 0
                        name_raw = item.get("file_name")
                        file_name = name_raw if isinstance(name_raw, str) else None
                        src_raw = item.get("source")
                        source = src_raw if isinstance(src_raw, str) and src_raw.strip() else f"attachment-{idx}"
                        result = gate.ingest(
                            RawAttachment(
                                source_id=source,
                                media_type=media_type.strip(),
                                size_bytes=size,
                                owner_scope=owner_scope,
                                content=content,
                                extracted_text=extracted,
                                file_name=file_name,
                            ),
                            authorized=True,
                            request_id=str(task_id),
                            token=task.token,
                        )
                        entry = result.to_dict()
                        entry["index"] = idx
                        observations_report.append(entry)
                        if result.accepted and result.observation is not None:
                            accepted_observations.append(result.observation)

                try:
                    if not agents_available():
                        raise AgentsBridgeError(
                            "the AURA agents runtime is not installed"
                        )
                    pipeline = service._pipeline()
                    agent = build_agent(
                        name=f"aura-agent-{str(task_id).removeprefix('rq-')[:8]}",
                        canonical=CanonicalContext(
                            brain=service.aura.brain,
                            memory=service.aura.brain.memory,
                            planning=pipeline.planning,
                            action_registry=pipeline.registry,
                            execution=pipeline.execution,
                        ),
                    )
                    outcome = run_agent_task(
                        agent=agent,
                        description=goal,
                        success_criteria=tuple(str(v) for v in criteria_raw),
                        capabilities=tuple(str(v) for v in capabilities_raw),
                        world_state=world_raw,
                        cancellation=task.token,
                        research=ResearchEngine(),
                        research_claims=research_claims,
                        research_evidence=research_evidence,
                        require_research=require_research,
                        observations=tuple(accepted_observations),
                    )
                except CancelledError:
                    task.cancelled_stage = "orchestration"
                    service._tasks.finish(task, status="cancelled", stage="orchestration")
                    self._send(
                        200,
                        {
                            "request_id": str(task_id),
                            "status": "cancelled",
                            "cancelled_stage": "orchestration",
                            "agent_id": None,
                            "success": False,
                            "reason": "agent task cancelled before start",
                            "iterations": 0,
                            "events": [],
                        },
                        correlation,
                    )
                    return
                except AgentsBridgeError:
                    service._tasks.finish(task, status="error")
                    self._error(
                        503,
                        "the AURA agents runtime is not installed",
                        correlation,
                        "agents.unavailable",
                    )
                    return
                except Exception as exc:  # noqa: BLE001 - a failed run is a report, never a crash
                    service._tasks.finish(task, status="error", error=str(exc))
                    self._send(
                        200,
                        {
                            "request_id": str(task_id),
                            "status": "error",
                            "agent_id": None,
                            "success": False,
                            "reason": f"agent runtime failure: {type(exc).__name__}",
                            "iterations": 0,
                            "events": [],
                        },
                        correlation,
                    )
                    return

                cancelled = outcome.cancelled
                status = "cancelled" if cancelled else "ok"
                payload: dict[str, Any] = {
                    "request_id": str(task_id),
                    "status": status,
                    "agent_id": outcome.agent_id,
                    "goal_id": outcome.goal_id,
                    "success": outcome.success,
                    "reason": outcome.reason,
                    "iterations": outcome.iterations,
                    "final_message": outcome.final_message,
                    "cancelled": cancelled,
                    "research": outcome.research,
                    "evaluation": outcome.evaluation,
                    "observations_report": observations_report,
                    "observations": outcome.observations,
                    "events": outcome.events,
                }
                if cancelled:
                    task.cancelled_stage = "agent"
                    payload["cancelled_stage"] = "agent"
                service._tasks.finish(task, status=status, result=payload)
                self._send(200, payload, correlation)

            def _handle_automation_create(self, body: dict[str, Any], correlation: CorrelationId, service: AuraApiServer) -> None:
                from aura.automation import AutomationStep

                manager = service._automation
                if manager is None:
                    self._error(503, "automation requires the AURA agents runtime", correlation, "agents.unavailable")
                    return
                goal = body.get("goal")
                if not isinstance(goal, str) or not goal.strip():
                    self._error(400, "field 'goal' is required and must be a string", correlation, "api.validation")
                    return
                steps_raw = body.get("steps")
                if steps_raw is None:
                    steps_raw = [goal]
                if (
                    not isinstance(steps_raw, list)
                    or not steps_raw
                    or len(steps_raw) > 20
                    or not all(isinstance(s, str) and s.strip() for s in steps_raw)
                ):
                    self._error(400, "field 'steps' must be a list of at most 20 non-empty strings (or omitted for a single step)", correlation, "api.validation")
                    return
                description = body.get("description")
                description = description if isinstance(description, str) and description.strip() else goal
                budget_limits: dict[str, float] | None = None
                budget_raw = body.get("budget")
                if budget_raw is not None:
                    if not isinstance(budget_raw, dict):
                        self._error(400, "field 'budget' must be an object of dimension->limit", correlation, "api.validation")
                        return
                    try:
                        budget_limits = {
                            str(k): float(v)
                            for k, v in budget_raw.items()
                            if isinstance(v, (int, float)) and float(v) >= 0
                        }
                    except (TypeError, ValueError):
                        budget_limits = {}
                    if not budget_limits:
                        self._error(400, "field 'budget' must contain at least one non-negative numeric limit", correlation, "api.validation")
                        return
                owner = self._owner_scope()
                # Automation steps only ever carry the server-side inert echo
                # capability; the client cannot supply arbitrary capabilities.
                steps = [AutomationStep(s, capabilities=("actions.echo",), success_criteria=("completed == True",)) for s in steps_raw]
                task_id = manager.submit(
                    owner=owner,
                    description=description,
                    steps=steps,
                    budget_limits=budget_limits,
                )
                service.audit.record(
                    action="automation.task.create",
                    actor=owner,
                    resource=str(task_id),
                    decision="allow",
                    reason="owner-created automation task",
                    correlation_id=str(correlation),
                )
                summary = manager.get(task_id, owner=owner)
                payload = {"task_id": task_id, "owner": owner, **(summary or {})}
                self._send(201, payload, correlation)

            def _handle_automation_list(self, correlation: CorrelationId, service: AuraApiServer) -> None:
                manager = service._automation
                if manager is None:
                    self._error(503, "automation requires the AURA agents runtime", correlation, "agents.unavailable")
                    return
                self._send(200, {"tasks": manager.list_tasks(self._owner_scope())}, correlation)

            def _handle_automation_inspect(self, path: str, correlation: CorrelationId, service: AuraApiServer) -> None:
                manager = service._automation
                if manager is None:
                    self._error(503, "automation requires the AURA agents runtime", correlation, "agents.unavailable")
                    return
                parts = path.split("/v1/automation/tasks/", 1)[1].split("/")
                task_id = parts[0]
                owner = self._owner_scope()
                if len(parts) >= 2 and parts[1] == "checkpoints":
                    cps = manager.checkpoints(task_id, owner=owner)
                    if cps is None:
                        self._error(404, f"automation task not found or not owned: {task_id}", correlation, "api.not_found")
                        return
                    self._send(200, {"task_id": task_id, "checkpoints": cps}, correlation)
                    return
                summary = manager.get(task_id, owner=owner)
                if summary is None:
                    self._error(404, f"automation task not found or not owned: {task_id}", correlation, "api.not_found")
                    return
                self._send(200, {"task_id": task_id, **summary}, correlation)

            def _handle_automation_action(self, path: str, correlation: CorrelationId, service: AuraApiServer) -> None:
                manager = service._automation
                if manager is None:
                    self._error(503, "automation requires the AURA agents runtime", correlation, "agents.unavailable")
                    return
                parts = path.split("/v1/automation/tasks/", 1)[1].split("/")
                task_id = parts[0]
                if len(parts) < 2:
                    self._error(404, f"unknown automation endpoint {path}", correlation, "api.not_found")
                    return
                action = parts[1]
                owner = self._owner_scope()
                if action == "pause":
                    out = manager.pause(task_id, owner=owner)
                elif action == "resume":
                    out = manager.resume(task_id, owner=owner)
                elif action == "cancel":
                    out = manager.cancel(task_id, owner=owner)
                elif action == "run":
                    out = manager.run(task_id, owner=owner)
                elif action == "retry":
                    step_part = parts[2] if len(parts) > 2 else None
                    step = int(step_part) if step_part is not None and step_part.isdigit() else None
                    out = manager.retry(task_id, owner=owner, step=step)
                else:
                    self._error(404, f"unknown automation action {action!r}", correlation, "api.not_found")
                    return
                if out is None:
                    self._error(404, f"automation task not found or not owned: {task_id}", correlation, "api.not_found")
                    return
                self._send(200, {"task_id": task_id, **out}, correlation)

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
                requested_scope = body.get("scope")
                if requested_scope is not None and not isinstance(requested_scope, str):
                    self._error(400, "field 'scope' must be a string when provided", correlation, "api.validation")
                    return
                scope = self._scoped_owner_scope(requested_scope)
                memory_id = service.aura.remember(key=key, content=content, kind=kind, importance=float(importance), scope=scope)
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
                requested_scope = body.get("scope")
                if requested_scope is not None and not isinstance(requested_scope, str):
                    self._error(400, "field 'scope' must be a string when provided", correlation, "api.validation")
                    return
                scope = self._scoped_owner_scope(requested_scope)
                self._send(200, {"entries": service.aura.recall(text, limit=limit, scope=scope)}, correlation)

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
                output = service.aura.research(
                    question,
                    claims=tuple(str(c) for c in claims),
                    evidence=evidence,
                    scope=self._owner_scope(),
                )
                self._send(200, output, correlation)

            def _handle_note_body(self, body: dict[str, Any], correlation: CorrelationId) -> tuple[str, str, str] | None:
                title = body.get("title")
                content = body.get("content")
                scope = body.get("scope", "owner:anonymous")
                if not isinstance(title, str) or not title.strip() or len(title) > 200:
                    self._error(400, "field 'title' is required and must be <= 200 chars", correlation, "api.validation")
                    return None
                if not isinstance(content, str) or len(content) > 65_536:
                    self._error(400, "field 'content' must be a string <= 65536 chars", correlation, "api.validation")
                    return None
                if not isinstance(scope, str) or not scope.strip():
                    self._error(400, "field 'scope' must be a non-empty string", correlation, "api.validation")
                    return None
                return title, content, scope

            def _notes(self, owner_scope: str) -> list[dict[str, object]]:
                from aura.memory.engine import MemoryQuery
                from aura.memory.models import MemoryType

                entries = service.aura.brain.memory.recall(
                    MemoryQuery(kind=MemoryType.SEMANTIC, scope=owner_scope, limit=500)
                )
                notes = []
                for entry in entries:
                    if not entry.key.startswith("note:"):
                        continue
                    notes.append(
                        {
                            "note_id": str(entry.id),
                            "title": entry.content.get("title", ""),
                            "content": entry.content.get("content", ""),
                            "scope": entry.scope,
                            "created_at": entry.created_at.isoformat() if entry.created_at else None,
                        }
                    )
                return notes

            def _handle_create_note(self, body: dict[str, Any], correlation: CorrelationId) -> None:
                parsed = self._handle_note_body(body, correlation)
                if parsed is None:
                    return
                title, content, requested_scope = parsed
                scope = self._scoped_owner_scope(requested_scope)
                from aura.foundation.ids import new_hex
                from aura.memory.models import MemoryType, Provenance

                entry = service.aura.brain.memory.remember(
                    key=f"note:{new_hex()}",
                    kind=MemoryType.SEMANTIC,
                    content={"title": title, "content": content},
                    importance=0.3,
                    scope=scope,
                    provenance=Provenance(source="api.notes"),
                )
                service.audit.record(
                    action="notes.create", actor="system", resource=str(entry.id),
                    decision="allow", reason="note created", correlation_id=str(correlation),
                )
                self._send(
                    201,
                    {"note_id": str(entry.id), "title": title, "content": content, "scope": scope},
                    correlation,
                )

            def do_PATCH(self) -> None:
                correlation = CorrelationId.new()
                path = urlparse(self.path).path
                if not path.startswith("/v1/notes/"):
                    self._error(404, f"unknown endpoint {path}", correlation, "api.not_found")
                    return
                body = self._read_json()
                if not self._require_auth(correlation):
                    return
                if not self._check_rate_limit(correlation):
                    return
                if body is None:
                    self._error(400, "request body must be a JSON object", correlation, "api.invalid_json")
                    return
                note_id = path.split("/v1/notes/", 1)[1]
                parsed = self._handle_note_body(body, correlation)
                if parsed is None:
                    return
                title, content, requested_scope = parsed
                scope = self._scoped_owner_scope(requested_scope)
                from aura.foundation.ids import MemoryId
                entry = service.aura.brain.memory.by_id(MemoryId.from_str(note_id))
                if entry.scope != scope:
                    self._error(404, f"note not found: {note_id}", correlation, "api.not_found")
                    return
                entry.content = {"title": title, "content": content}
                service.aura.brain.memory.store.update(entry)
                service.audit.record(action="notes.update", actor="system", resource=note_id,
                                     decision="allow", reason="note updated", correlation_id=str(correlation))
                self._send(200, {"note_id": note_id, "title": title, "content": content, "scope": scope}, correlation)

            def do_DELETE(self) -> None:
                correlation = CorrelationId.new()
                path = urlparse(self.path).path
                if not path.startswith("/v1/notes/"):
                    self._error(404, f"unknown endpoint {path}", correlation, "api.not_found")
                    return
                if not self._require_auth(correlation):
                    return
                if not self._check_rate_limit(correlation):
                    return
                note_id = path.split("/v1/notes/", 1)[1]
                from aura.foundation.ids import MemoryId
                try:
                    entry = service.aura.brain.memory.by_id(MemoryId.from_str(note_id))
                except Exception:  # noqa: BLE001 - 404 for missing notes
                    self._error(404, f"note not found: {note_id}", correlation, "api.not_found")
                    return
                owner = self._owner_scope()
                if owner != "owner:anonymous" and not (entry.scope or "").startswith(f"{owner}/"):
                    self._error(404, f"note not found: {note_id}", correlation, "api.not_found")
                    return
                scope = entry.scope
                service.aura.brain.memory.forget(entry.id)
                service.audit.record(action="notes.delete", actor="system", resource=note_id,
                                     decision="allow", reason="note deleted", correlation_id=str(correlation))
                self._send(200, {"note_id": note_id, "deleted": True, "scope": scope}, correlation)

            def _handle_plan(self, body: dict[str, Any], correlation: CorrelationId) -> None:
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
                # Route through the SDK so plans are created by the brain's
                # canonical planner and flight-recorded (plan.created /
                # plan.rejected). The response contract is unchanged.
                result = service.aura.plan(goal=Goal.create(description=goal_text), tasks=tasks)
                self._send(
                    200,
                    {
                        "plan_created": result["plan_created"],
                        "plan_id": result.get("plan_id"),
                        "steps": result.get("steps", []),
                        "risk": result.get("risk"),
                        "issues": result.get("issues", []),
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

    def close(self) -> None:
        """Release application resources owned by the server.

        Cancels every in-flight request (so provider HTTP calls interrupt
        promptly), then closes the memory store connection and the
        distributed-state connection pool so database handles (e.g. the SQLite
        WAL file lock, the PostgreSQL pool threads) are released deterministically
        on shutdown instead of relying on process exit. Safe to call more than
        once; resources without a ``close`` (e.g. the in-memory store) are
        skipped.
        """
        self._tasks.cancel_all()
        store = getattr(getattr(getattr(self.aura, "brain", None), "memory", None), "store", None)
        close_store = getattr(store, "close", None)
        if callable(close_store):
            close_store()
        state = getattr(self, "_distributed_state", None)
        close_state = getattr(state, "close", None)
        if callable(close_state):
            close_state()

    def run(self) -> None:
        server = ThreadingHTTPServer((self.config.host, self.config.port), self._handler())
        self.logger.info("aura-api listening", host=self.config.host, port=str(self.config.port))
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            self.logger.info("aura-api shutting down")
        finally:
            server.server_close()
            self.close()


def _env_float(name: str, *, default: float) -> float:
    raw = os.environ.get(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return float(raw)
    except ValueError:
        return default


def _provider_state_payload(service: AuraApiServer) -> dict[str, Any]:
    """Truthful provider status for ``GET /v1/providers``.

    Reports the distinction that matters to an operator: an adapter being
    *registered* is not a language model being *configured and running*. No
    credential material appears here -- the manager never exposes the key, and
    this payload deliberately carries only names, models and states.
    """
    manager = service.aura.brain.provider_manager
    if manager is None:
        return {
            "language_model_configured": False,
            "reason": (
                "no language model provider is configured; AURA reasons over saved "
                "memory and stored knowledge with deterministic strategies"
            ),
            "count": 0,
            "providers": [],
        }
    payload: dict[str, Any] = dict(manager.provider_state())
    payload["language_model_configured"] = bool(payload.get("configured"))
    return payload


def run_server(host: str | None = None, port: int | None = None) -> None:
    """Run the API server.

    Configuration is loaded from layered sources (env/file); ``AURA_ENVIRONMENT``,
    ``AURA_CONFIG``, and ``AURA_STORAGE_BACKEND`` are honored. Host and port
    resolve as: explicit argument > ``AURA_API_HOST`` / ``AURA_API_PORT`` env >
    defaults (``127.0.0.1:8765``). Production-mode
    gates: persistent backend REQUIRED, issuer secret REQUIRED (>= 16 chars),
    and the server fails fast with a clear error instead of silently falling
    back to unsafe defaults.
    """
    if host is None:
        host = os.environ.get("AURA_API_HOST", "").strip() or "127.0.0.1"
    if port is None:
        raw_port = os.environ.get("AURA_API_PORT", "").strip()
        if not raw_port:
            port = 8765
        else:
            try:
                port = int(raw_port)
            except ValueError as exc:
                raise ConfigurationError(
                    f"AURA_API_PORT must be an integer, got {raw_port!r}"
                ) from exc
    from aura.config.loader import ConfigLoader

    config = ConfigLoader().load()
    if os.environ.get("AURA_ENVIRONMENT") == "production":
        if config.storage.backend == "memory":
            raise ConfigurationError(
                "production run requires storage.backend = 'sqlite' (or 'postgresql'); "
                "refusing to serve with in-memory storage"
            )
        if config.storage.backend == "postgresql" and not config.storage.postgresql_dsn:
            raise ConfigurationError(
                "production run with storage.backend='postgresql' requires "
                "AURA_STORAGE_POSTGRESQL_DSN; refusing to serve"
            )
        api_secret = os.environ.get("AURA_API_SECRET", "")
        if not api_secret or len(api_secret) < 16:
            raise ConfigurationError(
                "production run requires AURA_API_SECRET (>= 16 characters); "
                "refusing to serve with a weak or missing issuer secret"
            )
    server_config = ServerConfig(
        host=host,
        port=port,
        api_key=os.environ.get("AURA_API_KEY") or None,
        api_secret=os.environ.get("AURA_API_SECRET") or None,
        admin_key=os.environ.get("AURA_API_ADMIN_KEY") or None,
        trust_proxy=_env_bool("AURA_API_TRUST_PROXY", default=False),
        rate_burst=int(_env_float("AURA_API_RATE_BURST", default=60.0)),
        rate_per_second=_env_float("AURA_API_RATE_PER_SECOND", default=1.0),
        max_request_bytes=int(_env_float("AURA_API_MAX_REQUEST_BYTES", default=1_048_576.0)),
        allow_pipeline=_env_bool("AURA_API_ALLOW_PIPELINE", default=False),
        distributed_state_dsn=os.environ.get("AURA_API_DISTRIBUTED_STATE_DSN") or None,
        distributed_state_policy=os.environ.get("AURA_API_DISTRIBUTED_STATE_POLICY", "fail_closed"),
        session_ttl_seconds=_env_float("AURA_API_SESSION_TTL_SECONDS", default=86400.0),
    )
    AuraApiServer(
        config=server_config,
        aura_config=config,
    ).run()


def _env_bool(name: str, *, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None or raw.strip() == "":
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


if __name__ == "__main__":
    run_server(host=sys.argv[1] if len(sys.argv) > 1 else None)

__all__ = ["AuraApiServer", "OPENAPI", "ServerConfig", "run_server"]