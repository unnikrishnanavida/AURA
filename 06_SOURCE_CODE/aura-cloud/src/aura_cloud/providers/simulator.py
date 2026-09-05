"""Simulated cloud provider for aura-cloud.

EXPLICITLY LABELED **SIMULATION**: this provider never talks to a real cloud.
It implements the full :class:`CloudProvider` contract so orchestration and
policy logic can be exercised end-to-end without credentials. Its ``kind`` is
``"simulation"`` and every result carries that label; nothing here is a real
AWS/Azure/GCP deployment.
"""

from __future__ import annotations

from typing import Any

from aura_cloud.providers.contracts import BaseCloudProvider, DeploymentResult


class SimulatedProvider(BaseCloudProvider):
    """An in-memory provider that implements plan/deploy/rollback/health."""

    kind = "simulation"
    name = "simulated"

    def __init__(self, *, fail_on_deploy: bool = False) -> None:
        self._deployed: dict[str, dict[str, Any]] = {}
        self.fail_on_deploy = fail_on_deploy

    def capabilities(self) -> set[str]:
        return {"compute", "storage", "network"}

    def plan(self, intent: Any) -> dict[str, Any]:
        if not getattr(intent, "workload", None):
            raise ValueError("intent requires a workload name")
        return {"intent": intent.workload, "simulated": True, "kind": self.kind}

    def deploy(self, plan: Any) -> DeploymentResult:
        if self.fail_on_deploy:
            return DeploymentResult(
                deployed=False,
                provider=self.name,
                detail="simulated deployment failure (injected)",
            )
        plan_id = getattr(plan, "plan_id", "plan-unknown")
        self._deployed[plan_id] = {"kind": self.kind, "plan_id": plan_id}
        return DeploymentResult(
            deployed=True,
            provider=self.name,
            detail=f"simulated deployment of {plan_id}",
            artifacts={"simulated": True, "plan_id": plan_id},
        )

    def rollback(self, plan: Any) -> DeploymentResult:
        plan_id = getattr(plan, "plan_id", "plan-unknown")
        self._deployed.pop(plan_id, None)
        return DeploymentResult(
            deployed=False,
            provider=self.name,
            detail=f"simulated rollback of {plan_id}",
        )

    def health(self) -> dict[str, Any]:
        return {"provider": self.name, "kind": self.kind, "status": "ok", "deployments": len(self._deployed)}


__all__ = ["SimulatedProvider"]