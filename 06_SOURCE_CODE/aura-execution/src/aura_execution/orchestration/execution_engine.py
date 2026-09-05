"""High-level execution engine for aura-execution.

Composes the existing orchestrator (which owns capability/permission/safety
gates, preparation, dispatch, observation, validation) with the cross-cutting
runtime guarantees:

- timeout enforcement
- cooperative cancellation
- retry with explicit classification (transient vs permanent)
- idempotency (repeat with the same key returns the recorded outcome)
- dry-run / simulation (never invokes the handler)
- rollback / compensation (only from pre-registered undo/compensate actions)

This engine does NOT re-implement security gates: it calls ``Orchestrator``
and enforces the runtime guarantees around it.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from aura_execution.contracts.requests.execution_request import ExecutionRequest
from aura_execution.contracts.responses.execution_result import ExecutionResult
from aura_execution.contracts.responses.execution_status import ExecutionStatus
from aura_execution.orchestration.orchestrator import Orchestrator
from aura_execution.runtime.cancellation import (
    CancellationScope,
    CancellationToken,
    Cancelled,
)
from aura_execution.runtime.dry_run import DryRunMode
from aura_execution.runtime.idempotency import IdempotencyGuard
from aura_execution.runtime.retries import RetryPolicy
from aura_execution.runtime.rollback import CompensationRegistry, RollbackCoordinator
from aura_execution.runtime.timeouts import TimeoutError, TimeoutGuard


@dataclass
class ExecutionEngine:
    """Wraps Orchestrator with runtime durability guarantees."""

    orchestrator: Orchestrator = field(default_factory=Orchestrator.default)
    timeout_seconds: float = 30.0
    retry_policy: RetryPolicy = field(default_factory=RetryPolicy)
    idempotency: IdempotencyGuard = field(default_factory=IdempotencyGuard)
    dry_run: DryRunMode = field(default_factory=DryRunMode)
    rollback: RollbackCoordinator = field(default_factory=RollbackCoordinator)
    compensations: CompensationRegistry = field(default_factory=CompensationRegistry)
    scope: CancellationScope = field(default_factory=CancellationScope)

    def register_capability(self, capability: Any) -> None:
        self.orchestrator.register_capability(capability)

    def execute(
        self,
        request: ExecutionRequest,
        *,
        principal: str = "system",
        idempotency_key: str | None = None,
        token: CancellationToken | None = None,
    ) -> ExecutionResult:
        """Execute a request with timeouts, cancellation, retries, idempotency,
        dry-run, and rollback support."""
        token = token or self.scope.child()
        action = request.action
        state = dict(request.state)

        # 1. Dry-run: validate WITHOUT side effects.
        if self.dry_run.enabled:
            return self._dry_run(request, token)

        # 2. Idempotent repeat: recorded outcome is replayed.
        if idempotency_key is not None:
            prior = self.idempotency.store.get(idempotency_key)
            if prior is not None:
                return ExecutionResult(
                    execution_id=prior.get("execution_id", "replayed"),
                    status=ExecutionStatus.SUCCEEDED,
                    result=prior.get("value"),
                    reason="idempotent replay",
                )

        # 3. Retriable execution loop.
        attempt = 0
        while True:
            try:
                token.check()
                result = self._run_once(request, principal, token, state)
            except Cancelled as exc:
                return ExecutionResult(
                    execution_id=str(action.action_id),
                    status=ExecutionStatus.CANCELLED,
                    reason=str(exc),
                )
            except TimeoutError as exc:
                return ExecutionResult(
                    execution_id=str(action.action_id),
                    status=ExecutionStatus.FAILED,
                    reason=f"timeout: {exc}",
                )

            if result.status in (ExecutionStatus.SUCCEEDED, ExecutionStatus.DENIED, ExecutionStatus.REVIEW, ExecutionStatus.BLOCKED):
                if result.status is ExecutionStatus.SUCCEEDED and idempotency_key is not None:
                    self.idempotency.store.put(idempotency_key, {"success": True, "execution_id": result.execution_id, "value": getattr(result.result, "value", None)})
                return result

            # FAILED -> decide whether to retry.
            should_retry, reason = self.retry_policy.should_retry(result.reason or "unknown", attempt)
            if not should_retry:
                self._finalize_failure(request, state, reason)
                return result
            attempt += 1
            time.sleep(self.retry_policy.backoff_seconds)

    # ------------------------------------------------------------------
    # internals
    # ------------------------------------------------------------------
    def _run_once(
        self,
        request: ExecutionRequest,
        principal: str,
        token: CancellationToken,
        state: dict[str, Any],
    ) -> ExecutionResult:
        action = request.action
        timeout = getattr(action, "timeout", self.timeout_seconds) or self.timeout_seconds
        token.check()

        orchestrator = self.orchestrator
        handler = getattr(action, "handler", None)

        if handler is not None and timeout > 0:
            guard = TimeoutGuard(timeout=float(timeout))

            def guarded_handler(*args: Any, **kwargs: Any) -> Any:
                token.check()
                _, value = guard.run(handler, *args, **kwargs)
                return value

            from dataclasses import replace

            action = replace(action, handler=guarded_handler)
            request = ExecutionRequest(
                action=action,
                inputs=request.inputs,
                state=request.state,
                approved=request.approved,
                budget=request.budget,
            )

        result = orchestrator.execute(request, principal=principal)
        if result.status is ExecutionStatus.SUCCEEDED:
            undo = getattr(action, "undo", None)
            if callable(undo):
                self.rollback.register_undo(getattr(action, "action_id", "?"), undo)
        return result

    def _dry_run(self, request: ExecutionRequest, token: CancellationToken) -> ExecutionResult:
        token.check()
        action = request.action
        simulation = self.dry_run.simulate(action, dict(request.inputs), None)
        return ExecutionResult(
            execution_id=str(action.action_id),
            status=ExecutionStatus.SUCCEEDED,
            result=simulation,
            reason="dry run (handler not invoked)",
        )

    def _finalize_failure(self, request: ExecutionRequest, state: dict[str, Any], reason: str) -> None:
        action = request.action
        action_id = getattr(action, "action_id", "?")
        if getattr(action, "reversible", False):
            self.rollback.rollback(state, action_ids=[action_id])
        if self.compensations.has(action_id):
            self.compensations.compensate(action_id, state)


__all__ = ["ExecutionEngine"]