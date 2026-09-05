"""Execution engine.

Guarded pipeline for every action:

  resolve action -> capability gate -> permission gate -> safety gate
  -> autonomy gate -> budget gate -> timeout + cancellation wrapped handler
  -> idempotency check -> result validation -> optional retry -> effect record

WorldState and ActionInputs are strictly separate. Effects are declared and
must be recorded; the engine never lets the world value be mutated implicitly.
"""

from __future__ import annotations

import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, cast

from aura.execution.models import ActionResult, ActionSpec, WorldState
from aura.execution.registry import ActionRegistry
from aura.foundation.cancellation import CancellationToken
from aura.foundation.errors import AuraTimeoutError, ValidationError
from aura.foundation.ids import ExecutionId, ToolCallId
from aura.security.guardrails import GuardrailService


@dataclass
class ExecutionRequest:
    """One requested action execution."""

    action: str
    inputs: Any
    world_state: WorldState
    execution_id: ExecutionId = field(default_factory=ExecutionId.new)
    approval: bool = False
    checkpoints: bool = True


@dataclass
class ExecutionResult:
    """Outcome of an execution request including the guardrail trace."""

    request: ExecutionRequest
    action_result: ActionResult
    attempts: int = 1
    guardrail_stages: list[dict[str, object]] = field(default_factory=list)
    new_world_state: WorldState | None = None
    replayed: bool = False

    @property
    def ok(self) -> bool:
        return self.action_result.ok

    def to_dict(self) -> dict[str, Any]:
        return {
            "execution_id": str(self.request.execution_id),
            "action": self.request.action,
            "ok": self.ok,
            "attempts": self.attempts,
            "replayed": self.replayed,
            "guardrail_stages": self.guardrail_stages,
            "result": self.action_result.to_dict(),
            "new_world_state": self.new_world_state.to_dict() if self.new_world_state else None,
        }


class _Timeout:
    """Bounded-execution guard: runs the wrapped callable on a worker thread
    and returns only if it completes within the budget."""

    def __init__(self, seconds: float) -> None:
        self.seconds = seconds

    def run(self, fn: Callable[[], ActionResult]) -> ActionResult:
        outcome: dict[str, Any] = {}
        worker = threading.Thread(target=self._call, args=(fn, outcome), daemon=True)
        worker.start()
        worker.join(timeout=self.seconds)
        if worker.is_alive():
            raise AuraTimeoutError(f"action exceeded timeout of {self.seconds}s")
        if "error" in outcome:
            error = outcome["error"]
            assert isinstance(error, BaseException)
            raise error
        return cast(ActionResult, outcome["value"])

    @staticmethod
    def _call(fn: Callable[[], ActionResult], outcome: dict[str, Any]) -> None:
        try:
            outcome["value"] = fn()
        except Exception as exc:  # propagate to the caller thread
            outcome["error"] = exc


class ExecutionEngine:
    def __init__(
        self,
        *,
        registry: ActionRegistry,
        guardrails: GuardrailService,
    ) -> None:
        self._registry = registry
        self._guardrails = guardrails
        self._lock = threading.RLock()
        self._seen_calls: set[str] = set()

    def execute(
        self,
        request: ExecutionRequest,
        *,
        cancellation: CancellationToken | None = None,
    ) -> ExecutionResult:
        spec = self._registry.get(request.action)
        token = cancellation or CancellationToken()

        gate = self._guardrails.check(
            action=spec.capability,
            resource=request.action,
            risk=spec.risk,
            approval=request.approval,
        )
        if not gate.allowed:
            return ExecutionResult(
                request=request,
                action_result=ActionResult(ok=False, tool_call_id=ToolCallId.new(), error=gate.reason),
                guardrail_stages=gate.stages,
            )

        try:
            self._check_preconditions(spec, request.world_state)
        except ValidationError as exc:
            return ExecutionResult(
                request=request,
                action_result=ActionResult(ok=False, tool_call_id=ToolCallId.new(), error=str(exc)),
                guardrail_stages=gate.stages,
            )

        call_key = self._call_key(request)
        replayed = False
        with self._lock:
            if spec.idempotent and call_key in self._seen_calls:
                replayed = True
            else:
                self._seen_calls.add(call_key)

        if replayed:
            return ExecutionResult(
                request=request,
                action_result=ActionResult(
                    ok=True,
                    tool_call_id=ToolCallId.new(),
                    output={"replayed": True},
                    execution_id=request.execution_id,
                    replayed=True,
                ),
                guardrail_stages=gate.stages,
                replayed=True,
            )

        attempt = 0
        last_error = ""
        while attempt <= spec.max_retries:
            attempt += 1
            try:
                token.check()
                result = self._run_once(spec, request, token)
                self._validate_result(spec, result)
                new_state = self._apply_effects(request.world_state, spec, result)
                return ExecutionResult(
                    request=request,
                    action_result=result,
                    attempts=attempt,
                    guardrail_stages=gate.stages,
                    new_world_state=new_state,
                )
            except AuraTimeoutError as exc:
                last_error = str(exc)
            except ValidationError as exc:
                last_error = str(exc)
            except Exception as exc:  # handler failure -> bounded retry
                last_error = str(exc)
            if attempt > spec.max_retries:
                break

        return ExecutionResult(
            request=request,
            action_result=ActionResult(
                ok=False,
                tool_call_id=ToolCallId.new(),
                error=last_error or "execution failed",
                execution_id=request.execution_id,
            ),
            attempts=attempt,
            guardrail_stages=gate.stages,
        )


    def _run_once(
        self, spec: ActionSpec, request: ExecutionRequest, token: CancellationToken
    ) -> ActionResult:
        import dataclasses

        started = time.monotonic()
        timeout = _Timeout(spec.timeout_seconds)

        def call() -> ActionResult:
            return spec.handler(request.inputs, token)

        result = timeout.run(call)
        if not isinstance(result, ActionResult):
            raise ValidationError(f"action {spec.name!r} did not return an ActionResult")
        duration_ms = (time.monotonic() - started) * 1000.0
        return dataclasses.replace(result, duration_ms=duration_ms)

    @staticmethod
    def _check_preconditions(spec: ActionSpec, world: WorldState) -> None:
        missing = [p for p in spec.preconditions if not world.has(p)]
        if missing:
            raise ValidationError(f"preconditions not satisfied: {missing}")

    @staticmethod
    def _validate_result(spec: ActionSpec, result: ActionResult) -> None:
        if not result.ok:
            raise ValidationError(result.error or f"action {spec.name!r} failed")
        for effect in spec.expected_effects:
            if effect not in result.output:
                raise ValidationError(f"expected effect {effect!r} missing from action output")

    def _apply_effects(
        self, world: WorldState, spec: ActionSpec, result: ActionResult
    ) -> WorldState | None:
        if not spec.declare_world_changes:
            return None
        changes = {
            effect: result.output.get(effect)
            for effect in spec.expected_effects
            if effect in result.output
        }
        return world.update(**changes) if changes else world

    @staticmethod
    def _call_key(request: ExecutionRequest) -> str:
        import json

        return f"{request.action}:{json.dumps(request.inputs.to_dict(), sort_keys=True)}"


__all__ = ["ExecutionEngine", "ExecutionRequest", "ExecutionResult"]
