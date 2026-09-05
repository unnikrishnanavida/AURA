"""Guardrail gate.

The fixed-order execution gate through which every action must pass:

  capability -> permission -> safety -> autonomy -> budget

A hard denial from any earlier stage short-circuits the pipeline and no later
stage can override it. The result records each stage decision and an
explanation for every step.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from aura.foundation.errors import (
    BudgetExhaustedError,
    CapabilityError,
    PermissionDeniedError,
    SafetyDeniedError,
)
from aura.security.autonomy import AutonomousDecision, AutonomyGate
from aura.security.budgets import BudgetTracker
from aura.security.capabilities import CapabilityRegistry
from aura.security.permissions import Decision, Identity, PolicyEngine
from aura.security.safety import SafetyDecision, SafetyEvaluator


@dataclass
class GuardrailResult:
    allowed: bool
    reason: str
    stages: list[dict[str, object]] = field(default_factory=list)
    approval_required: bool = False

    def to_dict(self) -> dict[str, object]:
        return {
            "allowed": self.allowed,
            "reason": self.reason,
            "approval_required": self.approval_required,
            "stages": self.stages,
        }


class GuardrailService:
    """Composes the security pipeline behind one stable entry point."""

    def __init__(
        self,
        *,
        capabilities: CapabilityRegistry | None = None,
        policies: PolicyEngine | None = None,
        safety: SafetyEvaluator | None = None,
        autonomy: AutonomyGate | None = None,
        budgets: BudgetTracker | None = None,
    ) -> None:
        self.capabilities = capabilities or CapabilityRegistry()
        self.policies = policies or PolicyEngine()
        self.safety = safety or SafetyEvaluator()
        self.autonomy = autonomy or AutonomyGate()
        self.budgets = budgets or BudgetTracker()

    def check(
        self,
        *,
        action: str,
        resource: str = "*",
        identity: Identity | None = None,
        risk: float = 0.0,
        approval: bool = False,
        cost: float = 0.0,
        tokens: int = 0,
    ) -> GuardrailResult:
        stages: list[dict[str, object]] = []

        if not self.capabilities.has(action):
            self._deny(stages, "capability", f"capability {action!r} not granted")
            return self._result(False, f"capability {action!r} not granted", stages)
        cap = self.capabilities.get(action)
        if not cap.available:
            self._deny(stages, "capability", f"capability {action!r} unavailable")
            return self._result(False, f"capability {action!r} unavailable", stages)
        stages.append({"stage": "capability", "decision": "ALLOW"})

        perm = self.policies.evaluate(action=action, resource=resource, identity=identity, risk=risk, approval=approval)
        stages.append({"stage": "permission", "decision": perm.decision.value, "reason": perm.reason})
        if perm.decision is Decision.DENY:
            return self._result(False, perm.reason, stages)
        if perm.decision is Decision.APPROVAL_REQUIRED:
            return self._result(False, perm.reason, stages, approval_required=True)

        safety = self.safety.evaluate(action=action, risk=risk)
        stages.append({"stage": "safety", "decision": safety.decision.value, "reason": safety.reason})
        if safety.decision is SafetyDecision.DENY:
            return self._result(False, safety.reason, stages)
        if safety.decision is SafetyDecision.REVIEW and not approval:
            return self._result(False, safety.reason, stages, approval_required=True)

        autonomy_result = self.autonomy.evaluate(risk, authorization_held=approval)
        stages.append({"stage": "autonomy", "decision": autonomy_result.decision.value, "reason": autonomy_result.reason})
        if autonomy_result.decision is AutonomousDecision.REQUIRES_APPROVAL:
            return self._result(False, autonomy_result.reason, stages, approval_required=True)

        try:
            self.budgets.consume(actions=1, cost=cost, tokens=tokens)
        except BudgetExhaustedError as exc:
            return self._result(False, str(exc), stages)
        stages.append({"stage": "budget", "decision": "ALLOW"})

        return GuardrailResult(allowed=True, reason="all guardrail stages passed", stages=stages)

    def enforce(self, **kwargs: Any) -> GuardrailResult:
        result = self.check(**kwargs)
        if not result.allowed and not result.approval_required:
            reason = result.reason
            stage = result.stages[-1]["stage"] if result.stages else "unknown"
            if stage == "capability":
                raise CapabilityError(reason)
            if stage == "permission":
                raise PermissionDeniedError(reason)
            if stage == "safety":
                raise SafetyDeniedError(reason)
            if stage == "budget":
                raise BudgetExhaustedError(reason)
            raise PermissionDeniedError(reason)
        return result

    @staticmethod
    def _result(allowed: bool, reason: str, stages: list[dict[str, object]], approval_required: bool = False) -> GuardrailResult:
        return GuardrailResult(allowed=allowed, reason=reason, stages=stages, approval_required=approval_required)

    @staticmethod
    def _deny(stages: list[dict[str, object]], stage: str, reason: str) -> None:
        stages.append({"stage": stage, "decision": "DENY", "reason": reason})


__all__ = ["GuardrailResult", "GuardrailService"]