"""Security domain tests: capabilities, permission policy, safety, budgets, autonomy, guardrails."""

from __future__ import annotations

import pytest

from aura.config.settings import BudgetLimits
from aura.foundation.errors import BudgetExhaustedError, CapabilityError, PermissionDeniedError
from aura.security.autonomy import AutonomousDecision, AutonomyGate, AutonomyMode
from aura.security.budgets import BudgetTracker
from aura.security.capabilities import Capability, CapabilityRegistry, name_matches
from aura.security.guardrails import GuardrailService
from aura.security.permissions import Decision, Identity, PolicyEngine, Rule
from aura.security.safety import SafetyDecision, SafetyEvaluator, SafetyPolicy


def test_name_matches() -> None:
    assert name_matches("filesystem.*", "filesystem.read")
    assert name_matches("filesystem.read", "filesystem.read")
    assert not name_matches("filesystem.write", "filesystem.read")
    assert name_matches("*", "anything.at.all")


def test_capability_registry() -> None:
    registry = CapabilityRegistry()
    registry.register(Capability(name="filesystem.read", scope="documents"))
    assert registry.has("filesystem.read")
    assert not registry.has("filesystem.write")
    assert registry.get("filesystem.read").scope == "documents"


def test_capability_denied() -> None:
    registry = CapabilityRegistry()
    with pytest.raises(CapabilityError):
        registry.require("missing.capability")


def test_policy_default_deny() -> None:
    policy = PolicyEngine()
    result = policy.evaluate(action="database.delete", resource="users")
    assert result.decision is Decision.DENY
    assert "default deny" in result.reason


def test_policy_allow() -> None:
    policy = PolicyEngine()
    policy.add_rule(Rule(action="filesystem.read", effect=Decision.ALLOW, name="read-rule"))
    result = policy.evaluate(action="filesystem.read")
    assert result.decision is Decision.ALLOW


def test_policy_approval_required() -> None:
    policy = PolicyEngine()
    policy.add_rule(
        Rule(action="database.delete", effect=Decision.ALLOW, requires_approval=True, name="del-rule")
    )
    assert policy.evaluate(action="database.delete").decision is Decision.APPROVAL_REQUIRED
    assert policy.evaluate(action="database.delete", approval=True).decision is Decision.ALLOW


def test_policy_risk_gate() -> None:
    policy = PolicyEngine()
    policy.add_rule(Rule(action="deploy", effect=Decision.ALLOW, risk_max=0.5, name="deploy-rule"))
    assert policy.evaluate(action="deploy", risk=0.9).decision is Decision.APPROVAL_REQUIRED
    assert policy.evaluate(action="deploy", risk=0.1).decision is Decision.ALLOW


def test_policy_enforce_denies() -> None:
    policy = PolicyEngine()
    with pytest.raises(PermissionDeniedError):
        policy.enforce(action="anything")


def test_safety_default_review_on_risk() -> None:
    evaluator = SafetyEvaluator()
    result = evaluator.evaluate(action="unknown.action", risk=0.4)
    assert result.decision is SafetyDecision.REVIEW


def test_safety_forbidden() -> None:
    policy = SafetyPolicy(forbidden_capabilities={"kernel.panic"})
    evaluator = SafetyEvaluator(policy=policy)
    assert evaluator.evaluate(action="kernel.panic", risk=0.0).decision is SafetyDecision.DENY


def test_safety_allow_low_risk() -> None:
    evaluator = SafetyEvaluator()
    assert evaluator.evaluate(action="echo.hello", risk=0.0).decision is SafetyDecision.ALLOW


def test_autonomy_requires_approval() -> None:
    gate = AutonomyGate(AutonomyMode.SUPERVISED)
    assert gate.evaluate(0.1).decision is AutonomousDecision.APPROVED
    assert gate.evaluate(0.9).decision is AutonomousDecision.REQUIRES_APPROVAL


def test_budget_exhaustion() -> None:
    tracker = BudgetTracker(limits=BudgetLimits(max_actions=1))
    with pytest.raises(BudgetExhaustedError):
        tracker.consume(actions=1)  # consume self-checks after increment


def test_budget_seconds_limit() -> None:
    tracker = BudgetTracker(limits=BudgetLimits(max_seconds=0.001))
    import time

    time.sleep(0.01)
    with pytest.raises(BudgetExhaustedError):
        tracker.check()


def test_guardrail_capability_deny_short_circuits() -> None:
    service = GuardrailService()
    result = service.check(action="tools.unsafe", identity=Identity("alice"))
    assert not result.allowed
    assert result.stages[0]["stage"] == "capability"

    with pytest.raises(CapabilityError):
        service.enforce(action="tools.unsafe", identity=Identity("alice"))


def test_guardrail_full_allow() -> None:
    service = GuardrailService()
    service.capabilities.register(Capability(name="echo.hello"))
    service.policies.add_rule(Rule(action="echo.hello", effect=Decision.ALLOW))
    result = service.check(action="echo.hello", identity=Identity("alice"), risk=0.0)
    assert result.allowed
    assert result.stages[-1]["stage"] == "budget"


def test_guardrail_approval_required() -> None:
    service = GuardrailService()
    service.capabilities.register(Capability(name="db.delete"))
    service.policies.add_rule(Rule(action="db.delete", effect=Decision.ALLOW, requires_approval=True))
    result = service.check(action="db.delete", identity=Identity("alice"))
    assert not result.allowed
    assert result.approval_required


def test_guardrail_approval_required_returns_result() -> None:
    service = GuardrailService()
    service.capabilities.register(Capability(name="db.delete"))
    service.policies.add_rule(Rule(action="db.delete", effect=Decision.ALLOW, requires_approval=True))
    result = service.enforce(action="db.delete", identity=Identity("bob"))
    assert not result.allowed
    assert result.approval_required