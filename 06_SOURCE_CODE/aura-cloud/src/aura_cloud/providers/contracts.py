"""Cloud provider contracts for aura-cloud.

THIS IS AN INTERFACE. No real AWS/Azure/GCP SDK integration is implemented in
this repo. Providers implementing :class:`CloudProvider` may be either real
(behind an adapter, elsewhere) or a :class:`SimulatedProvider`; runtime code
only depends on the protocol. Deployments are never faked: a provider must
implement ``deploy`` and return a truthful result, and the simulation provider
is explicitly labeled ``kind="simulation"``.
"""

from __future__ import annotations

import abc
from dataclasses import dataclass, field
from typing import Any, Protocol


class CapabilityProvider(Protocol):
    """Anything that can enumerate its cloud capabilities."""

    def capabilities(self) -> set[str]: ...


@dataclass(frozen=True)
class DeploymentResult:
    """Truthful result of a deployment attempt."""

    deployed: bool
    provider: str
    detail: str
    artifacts: dict[str, Any] = field(default_factory=dict)


class CloudProvider(Protocol):
    """The single provider contract for aura-cloud."""

    name: str
    kind: str  # "real" | "simulation" | "mock"

    def capabilities(self) -> set[str]: ...
    def plan(self, intent: Any) -> Any: ...
    def deploy(self, plan: Any) -> DeploymentResult: ...
    def rollback(self, plan: Any) -> DeploymentResult: ...
    def health(self) -> dict[str, Any]: ...


class BaseCloudProvider(abc.ABC):
    """Shared, honest defaults for cloud providers."""

    kind: str = "interface"

    @property
    @abc.abstractmethod
    def name(self) -> str: ...

    @abc.abstractmethod
    def capabilities(self) -> set[str]: ...

    @abc.abstractmethod
    def plan(self, intent: Any) -> Any: ...

    def deploy(self, plan: Any) -> DeploymentResult:
        # INTERFACE default: real providers must override this.
        raise NotImplementedError(
            f"{self.name} ({self.kind}) does not implement deploy; "
            "real provider SDK integration must override this method"
        )

    def rollback(self, plan: Any) -> DeploymentResult:
        raise NotImplementedError(
            f"{self.name} ({self.kind}) does not implement rollback"
        )

    def health(self) -> dict[str, Any]:
        return {"provider": self.name, "kind": self.kind, "status": "unknown"}


__all__ = ["BaseCloudProvider", "CapabilityProvider", "CloudProvider", "DeploymentResult"]