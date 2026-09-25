"""Cloud deployment contracts (Phase 32).

Clean provider abstraction so deployment capability is *real code* with an
honest completion status for every operation:

- :class:`DeploymentStatus` marks each result as ``SIMULATED`` or ``LIVE``.
- :class:`CloudClient` is implemented by a local simulator
  (:mod:`aura.cloud.simulator`) for tests and by real adapters later; a real
  adapter is only LIVE when executed against a provider with credentials.

Credential and infra reality (2026-09-25): no cloud credentials were
available, so *every* execution in this phase is SIMULATED (deterministic local
implementation). Nothing here claims a live deployment.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Protocol


class Verification(StrEnum):
    SIMULATED = "simulated"
    UNIT_TESTED = "unit_tested"
    INTEGRATION_TESTED = "integration_tested"
    LIVE_VERIFIED = "live_verified"
    ENVIRONMENT_DEPENDENT = "environment_dependent"


@dataclass(frozen=True)
class DeploymentTarget:
    """What is being deployed and where."""

    environment: str
    region: str = "local"
    image: str = "aura:0.2.0"
    instance_count: int = 1


@dataclass(frozen=True)
class CloudPolicy:
    """Cost safety + IAM guards; violating them refuses the operation."""

    max_instances: int = 4
    budget_units: float = 100.0
    require_cleanup: bool = True
    require_iam_least_privilege: bool = True


@dataclass
class DeploymentResult:
    operation: str
    target: str
    status: Verification
    detail: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {"operation": self.operation, "target": self.target, "status": self.status.value, **self.detail}


class CloudClient(Protocol):
    """Provider contract: all ops are idempotent-ish and return plain dicts."""

    def provision(self, target: DeploymentTarget, *, inst_ct: int = 1) -> dict[str, Any]: ...
    def health(self, target: DeploymentTarget) -> dict[str, Any]: ...
    def scale(self, target: DeploymentTarget, inst_ct: int) -> dict[str, Any]: ...
    def deploy(self, target: DeploymentTarget) -> dict[str, Any]: ...
    def rollback(self, target: DeploymentTarget, to_revision: str | None = None) -> dict[str, Any]: ...


__all__ = ["CloudClient", "CloudPolicy", "DeploymentResult", "DeploymentTarget", "Verification"]