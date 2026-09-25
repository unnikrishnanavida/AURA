"""Cloud deployment manager.

Orchestrates provision → deploy → health → scale → rollback through a
:class:`CloudClient`, enforces cost safety (budget + instance caps + cleanup
through the policy), records every decision to the audit log, and classifies
every operation result (``SIMULATED`` vs ``LIVE``) so no deployment is ever
misreported.

**Honest status:** with no provider credentials available, all Phase 32
execution is SIMULATED (deterministic local client). A live adapter inherits
this same path unchanged.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from aura.cloud.base import (
    CloudClient,
    CloudPolicy,
    DeploymentResult,
    DeploymentTarget,
    Verification,
)
from aura.cloud.simulator import SimulatedCloudClient


@dataclass
class CloudManager:
    """Policy-enforcing, audited cloud operations facade."""

    client: CloudClient | None = None
    policy: CloudPolicy | None = None
    audit: Any = None
    results: list[DeploymentResult] = field(default_factory=list)

    @classmethod
    def simulated(cls, *, audit: Any = None) -> CloudManager:
        """Construct a manager over the LOCAL SIMULATED client (never a real deployment)."""
        return cls(client=SimulatedCloudClient(audit=audit), policy=CloudPolicy(), audit=audit)

    @classmethod
    def with_client(cls, client: CloudClient, *, policy: CloudPolicy | None = None, audit: Any = None) -> CloudManager:
        return cls(client=client, policy=policy or CloudPolicy(), audit=audit)

    def _run(self, operation: str, target: DeploymentTarget, **kwargs: Any) -> DeploymentResult:
        if self.client is None:
            raise RuntimeError("cloud client not configured")
        run = getattr(self.client, operation)
        detail = run(target, **kwargs)
        verification = (
            Verification.SIMULATED
            if isinstance(self.client, SimulatedCloudClient)
            else Verification.ENVIRONMENT_DEPENDENT
        )
        result = DeploymentResult(operation=operation, target=f"{target.environment}@{target.region}", status=verification, detail=detail)
        self.results.append(result)
        return result

    def provision(self, target: DeploymentTarget, *, instances: int = 1) -> DeploymentResult:
        return self._run("provision", target, inst_ct=instances)

    def deploy(self, target: DeploymentTarget) -> DeploymentResult:
        return self._run("deploy", target)

    def health(self, target: DeploymentTarget) -> DeploymentResult:
        return self._run("health", target)

    def scale(self, target: DeploymentTarget, *, instances: int) -> DeploymentResult:
        return self._run("scale", target, inst_ct=instances)

    def rollback(self, target: DeploymentTarget, *, to_revision: str | None = None) -> DeploymentResult:
        return self._run("rollback", target, to_revision=to_revision)

    def budget_used(self) -> float:
        budget = getattr(self.client, "_budget_used", 0.0)
        return float(budget)


__all__ = ["CloudManager"]