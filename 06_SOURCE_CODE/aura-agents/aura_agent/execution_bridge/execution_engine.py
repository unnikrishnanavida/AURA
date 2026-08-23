"""Execution engine: orchestrates the guarded execution pipeline.

Pipeline per execution:

    request validation
        -> capability match
        -> permission decision
        -> constitution check
        -> safety evaluation
        -> autonomy/approval gate
        -> budget check
        -> tool dispatch
        -> result validation
        -> state machine transitions
        -> flight-recorder events

Every stage is real orchestration. No subsystem independently overrides a
hard denial: capability, permission, constitution, and safety are applied in
a fixed authoritative order.
"""

from __future__ import annotations

import time as _time
from dataclasses import dataclass
from typing import Any, Protocol

from aura_agent.contracts.errors import (
    ApprovalRequired,
    BudgetExceeded,
    CapabilityDenied,
    PermissionDenied,
    SafetyDenied,
)
from aura_agent.contracts.ids import ExecutionId
from aura_agent.contracts.states import ExecutionState, StateMachine
from aura_agent.execution_bridge.requests.execution_request import ExecutionRequest
from aura_agent.execution_bridge.responses.execution_result import (
    ActionResult,
    ExecutionResult,
    FailureClass,
)
from aura_agent.flight_recorder.events.agent_event import AgentEvent
from aura_agent.tools.models import ToolContext

__all__ = ["ExecutionEngine", "ExecutionDependencies", "ExecContext"]


class ExecContext(Protocol):
    """Minimal flight-recorder contract consumed by the execution engine."""

    def record(self, event: AgentEvent) -> None: ...


@dataclass(frozen=True)
class ExecutionDependencies:
    """Injectable dependencies of the execution engine (no globals)."""

    tool_registry: Any
    capability_registry: Any
    policy_engine: Any
    constitution_checker: Any
    safety_evaluator: Any
    autonomy_engine: Any
    budget_engine: Any
    recorder: ExecContext | None = None
    clock=None
class ExecutionEngine:
    """Owns one guarded execution pipeline."""

    def __init__(self, deps: ExecutionDependencies) -> None:
        self._deps = deps
        self._clock = deps.clock or _time.time

    def execute(self, request: ExecutionRequest) -> ExecutionResult:
        """Run the full guarded pipeline for a single action request."""
        execution_id = request.execution_id or ExecutionId.new()
        request = request.with_execution_id(execution_id)
        machine = StateMachine(ExecutionState.PENDING)

        tool = self._deps.tool_registry.get(request.tool_name)
        if tool is None:
            return self._fail_with(
                machine, request, FailureClass.VALIDATION, f"unknown tool {request.tool_name!r}"
            )

        # -- 1. capability gate -------------------------------------------------
        cap = self._deps.capability_registry.match(request.capability)
        if cap.status.value != "match":
            raise CapabilityDenied(
                f"capability {request.capability!r} denied: {cap.reason}"
            )
        if tool.capability != request.capability:
            raise CapabilityDenied(
                f"tool {request.tool_name!r} provides {tool.capability!r}, "
                f"not {request.capability!r}"
            )

        # -- 2. permission gate --------------------------------------------------
        perm = self._deps.policy_engine.enforce(self._permission_request(request))
        if not perm.allowed:
            raise PermissionDenied("permission denied: " + "; ".join(perm.reasons))

        # -- 3. constitution gate -------------------------------------------------
        constit = self._deps.constitution_checker.check(
            str(request.action_id), request.capability
        )
        if not constit.allowed:
            if constit.verdict.value == "deny":
                raise PermissionDenied(
                    "constitution denied: " + "; ".join(constit.reasons)
                )
            raise ApprovalRequired(
                "constitution review: " + "; ".join(constit.reasons)
            )

        # -- 4. safety gate --------------------------------------------------------
        safety = self._deps.safety_evaluator.evaluate(self._safety_request(request))
        if not safety.allowed:
            if safety.decision.value == "deny":
                raise SafetyDenied("safety denied: " + "; ".join(safety.reasons))
            raise ApprovalRequired("safety review: " + "; ".join(safety.reasons))

        # -- 5. autonomy / approval gate -------------------------------------------
        approval = self._deps.autonomy_engine.requires_approval(
            risk_score=request.risk_score, action_name=request.tool_name
        )
        if approval.required:
            raise ApprovalRequired(approval.reason)

        # -- 6. budget gate -----------------------------------------------------
        budget = self._deps.budget_engine.acquire(execution_id)
        if budget is not None:
            projected = {
                "actions": 1.0,
                "time_s": tool.timeout_s,
                "cost": float(request.risk_score),
            }
            budget_check = self._deps.budget_engine.check_execution(
                execution_id, projection=projected
            )
            if not budget_check.allowed:
                raise BudgetExceeded(budget_check.reason)

        # -- 7. dispatch --------------------------------------------------------------
        machine.transition(ExecutionState.READY, reason="all gates passed")
        machine.transition(ExecutionState.RUNNING, reason="dispatch")
        self._record(request, "execution.started", {"tool": request.tool_name})
        context = ToolContext(
            execution_id=execution_id,
            agent_id=request.agent_id,
            goal_id=request.goal_id,
        )
        started = self._clock()
        try:
            tool_result = tool.execute(request.inputs, context=context)
        except Exception as exc:  # noqa: BLE001 - classified below
            failure = self._classify(exc)
            self._record(
                request,
                "execution.failed",
                {"error": str(exc), "class": failure.value},
            )
            machine.transition(ExecutionState.FAILED, reason=f"failed: {failure.value}")
            return ExecutionResult(
                execution_id=execution_id,
                success=False,
                results=[
                    ActionResult(
                        execution_id=execution_id,
                        action_id=str(request.action_id),
                        tool_name=request.tool_name,
                        success=False,
                        error=str(exc),
                        failure_class=failure,
                    )
                ],
                state=machine.state.value,
                finished_at=self._clock(),
            )

        duration = self._clock() - started
        if budget is not None:
            self._deps.budget_engine.consume(execution_id, dimension="actions", amount=1.0)
            self._deps.budget_engine.consume(execution_id, dimension="time_s", amount=duration)

        machine.transition(ExecutionState.SUCCEEDED, reason="tool returned")
        self._record(
            request,
            "execution.succeeded",
            {"tool": request.tool_name, "duration_s": duration},
        )
        action_result = ActionResult(
            execution_id=execution_id,
            action_id=str(request.action_id),
            tool_name=request.tool_name,
            success=True,
            output=tool_result.output,
            duration_s=duration,
            observed_effects=tool_result.observed_state,
        )
        return ExecutionResult(
            execution_id=execution_id,
            success=True,
            results=[action_result],
            state=machine.state.value,
            started_at=started,
            finished_at=self._clock(),
        )
# -- helpers ---------------------------------------------------------------
    def _record(
        self, request: ExecutionRequest, event_type: str, payload: dict
    ) -> None:
        if self._deps.recorder is None:
            return
        self._deps.recorder.record(
            AgentEvent(
                execution_id=request.execution_id,
                agent_id=request.agent_id,
                event_type=event_type,
                payload=payload,
            )
        )

    def _permission_request(self, request: ExecutionRequest):
        from aura_agent.policies.models import PermissionRequest

        return PermissionRequest(
            actor=request.agent_id,
            action=request.tool_name,
            resource=request.capability,
            risk_score=request.risk_score,
        )

    def _safety_request(self, request: ExecutionRequest):
        from aura_agent.policies.safety.safety_decision import SafetyRequest

        return SafetyRequest(
            action_name=request.tool_name,
            capability=request.capability,
            inputs=request.inputs,
            risk_score=request.risk_score,
        )

    @staticmethod
    def _classify(exc: Exception) -> FailureClass:
        from aura_agent.contracts.errors import (
            ActionTimeout,
            ApprovalRequired,
            BudgetExceeded,
            CapabilityDenied,
            PermissionDenied,
            SafetyDenied,
            ToolExecutionError,
            ValidationFailure,
        )

        if isinstance(exc, ActionTimeout):
            return FailureClass.TIMEOUT
        if isinstance(exc, BudgetExceeded):
            return FailureClass.RESOURCE
        if isinstance(
            exc,
            (CapabilityDenied, PermissionDenied, SafetyDenied, ApprovalRequired),
        ):
            return FailureClass.POLICY
        if isinstance(exc, (ToolExecutionError, ValidationFailure)):
            return FailureClass.VALIDATION
        return FailureClass.UNKNOWN

    def _fail_with(
        self,
        machine: StateMachine,
        request: ExecutionRequest,
        failure: FailureClass,
        error: str,
    ) -> ExecutionResult:
        machine.transition(ExecutionState.FAILED, reason=error)
        return ExecutionResult(
            execution_id=request.execution_id,  # type: ignore[arg-type]
            success=False,
            results=[
                ActionResult(
                    execution_id=request.execution_id,  # type: ignore[arg-type]
                    action_id=str(request.action_id),
                    tool_name=request.tool_name,
                    success=False,
                    error=error,
                    failure_class=failure,
                )
            ],
            state=machine.state.value,
            finished_at=self._clock(),
        )
