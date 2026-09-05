"""Tests for aura-cloud: provider contracts, simulation, budgets, rollback, audit.

No real AWS/Azure/GCP deployment is claimed. The SimulatedProvider is
explicitly labeled kind="simulation" and everything here exercises the
contracts without credentials.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from aura_cloud.deployment.rollback import RollbackLedger
from aura_cloud.engine import CloudControlPlane
from aura_cloud.finops.budget import CostBudget
from aura_cloud.ledger.change_events import DeploymentAudit
from aura_cloud.models import CloudIntent, DeploymentState, DeploymentPlan
from aura_cloud.providers.contracts import BaseCloudProvider
from aura_cloud.providers.simulator import SimulatedProvider


def _intent() -> CloudIntent:
    return CloudIntent(workload="web", region="us-east-1", capabilities=("compute",))


def test_simulated_provider_is_labeled_simulation():
    provider = SimulatedProvider()
    assert provider.kind == "simulation"
    assert "simulated" in provider.health()["status"] or provider.health()["provider"] == "simulated"


def test_control_plane_plans_through_simulation():
    plane = CloudControlPlane(SimulatedProvider())
    plan = plane.plan(_intent())
    assert plan.provider == "simulated"
    assert plan.state is DeploymentState.PLANNED


def test_control_plane_rejects_missing_capability():
    plane = CloudControlPlane(SimulatedProvider())
    intent = CloudIntent(workload="w", region="r", capabilities=("quantum-compute",))
    try:
        plane.plan(intent)
    except RuntimeError as exc:
        assert "capability gap" in str(exc)
    else:
        raise AssertionError("missing capability must raise")


def test_control_plane_rejects_high_risk():
    plane = CloudControlPlane(SimulatedProvider(), risk_budget=0.2)
    from aura_cloud.policy.guardrails import allow_plan

    assert allow_plan(0.9, 0.2) is False
    try:
        plane.plan(_intent(), risk=0.9)
    except PermissionError:
        pass
    else:
        raise AssertionError("high-risk deployment must be rejected")


def test_simulated_deploy_and_rollback_are_truthful():
    provider = SimulatedProvider()
    plan = DeploymentPlan("pl-1", "simulated", ("deploy:web",), 0.1)
    deployed = provider.deploy(plan)
    assert deployed.deployed is True
    assert deployed.provider == "simulated"
    assert deployed.artifacts["simulated"] is True
    rolled = provider.rollback(plan)
    assert rolled.deployed is False
    assert "rollback" in rolled.detail


def test_simulated_deploy_failure_is_not_faked():
    provider = SimulatedProvider(fail_on_deploy=True)
    plan = DeploymentPlan("pl-2", "simulated", (), 0.1)
    result = provider.deploy(plan)
    assert result.deployed is False  # honest failure, not fake success


def test_interface_provider_does_not_pretend_deploy():
    class _InterfaceOnly(BaseCloudProvider):
        name = "interface-only"

        def capabilities(self) -> set[str]:
            return set()

        def plan(self, intent):
            return {}

    try:
        _InterfaceOnly().deploy(None)
    except NotImplementedError:
        pass
    else:
        raise AssertionError("interface provider must not implement deploy")


def test_cost_budget_enforces_ceiling():
    budget = CostBudget(max_cost=100)
    assert budget.charge(60) is True
    assert budget.allows(30) is True
    assert budget.charge(50) is False  # would exceed 60+50 > 100
    assert budget.spent == 60
    assert budget.remaining == 40


def test_negative_cost_rejected():
    budget = CostBudget(max_cost=10)
    try:
        budget.charge(-5)
    except ValueError:
        pass
    else:
        raise AssertionError("negative cost must be rejected")


def test_rollback_ledger_append_only():
    ledger = RollbackLedger()
    ledger.record("pl-1", "simulated", "post-deploy misconfiguration")
    ledger.record("pl-1", "simulated", "health check failed")
    records = ledger.for_plan("pl-1")
    assert len(records) == 2
    assert len(ledger) == 2
    assert "health check failed" in records[-1].reason


def test_deployment_audit_trail():
    audit = DeploymentAudit()
    audit.record(plan_id="pl-1", event_type="planned", provider="simulated", detail="plan created")
    audit.record(plan_id="pl-1", event_type="deployed", provider="simulated", detail="deployed")
    audit.record(plan_id="pl-1", event_type="rolled_back", provider="simulated", detail="rolled back")
    events = audit.for_plan("pl-1")
    assert [e.event_type for e in events] == ["planned", "deployed", "rolled_back"]