"""Phase 32 cloud tests: lifecycle, cost safety, IAM guard, verification flags."""

from __future__ import annotations

from aura.cloud.base import CloudPolicy, DeploymentTarget, Verification
from aura.cloud.manager import CloudManager
from aura.security.audit import AuditLog


def _target(*, environment: str = "staging", region: str = "local", instances: int = 1) -> DeploymentTarget:
    return DeploymentTarget(environment=environment, region=region, instance_count=instances)


def test_full_lifecycle_is_simulated_and_audited() -> None:
    audit = AuditLog()
    manager = CloudManager.simulated(audit=audit)
    target = _target()
    provision = manager.provision(target, instances=2)
    assert provision.status is Verification.SIMULATED
    assert manager.deploy(target).status is Verification.SIMULATED
    health = manager.health(target)
    assert health.status is Verification.SIMULATED
    assert health.detail.get("healthy") is True
    assert manager.scale(target, instances=1).status is Verification.SIMULATED
    rollback = manager.rollback(target)
    assert rollback.status is Verification.SIMULATED
    assert any(r.action == "cloud.provision" for r in audit.entries())
    assert len(manager.results) == 5


def test_cost_safety_instance_cap() -> None:
    manager = CloudManager.simulated()
    try:
        manager.provision(_target(), instances=50)
        raise AssertionError("expected instance cap to refuse")
    except ValueError:
        pass


def test_cost_safety_budget() -> None:
    from aura.cloud.simulator import SimulatedCloudClient

    client = SimulatedCloudClient(policy=CloudPolicy(budget_units=1.0))
    manager = CloudManager(client=client, policy=CloudPolicy(budget_units=1.0))
    try:
        manager.provision(_target(), instances=1)
        raise AssertionError("expected budget refusal")
    except RuntimeError:
        pass


def test_iam_least_privilege_guard_for_non_local_regions() -> None:
    manager = CloudManager.simulated()
    non_local = _target(environment="prod", region="eu-west-1")
    try:
        manager.provision(non_local)
        raise AssertionError("expected iam least-privilege refusal for non-local region")
    except ValueError:
        pass


def test_operations_on_unprovisioned_target_fail_closed() -> None:
    manager = CloudManager.simulated()
    try:
        manager.deploy(_target())
        raise AssertionError("expected refusal to deploy to an unprovisioned target")
    except RuntimeError:
        pass


def test_custom_client_is_not_misreported_as_live() -> None:
    from aura.cloud.base import CloudClient

    class MyClient(CloudClient):
        def provision(self, target, *, inst_ct: int = 1) -> dict:
            return {"instances": inst_ct}

        def health(self, target) -> dict:
            return {"healthy": True}

        def scale(self, target, inst_ct: int) -> dict:
            return {"instances": inst_ct}

        def deploy(self, target) -> dict:
            return {"revision": "r1"}

        def rollback(self, target, to_revision: str | None = None) -> dict:
            return {}

    manager = CloudManager.with_client(MyClient())  # type: ignore[arg-type]
    result = manager.provision(_target())
    # Without a live adapter verification the status must not claim LIVE.
    assert result.status is Verification.ENVIRONMENT_DEPENDENT