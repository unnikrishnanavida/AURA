"""Cloud deployment support (Phase 32).

Provider abstraction + policy/safety controls + honest verification status.
**Phase 32 reality:** no cloud credentials were available; every execution is
SIMULATED (deterministic local client) and this is stated on every result.
"""

from aura.cloud.base import CloudPolicy, DeploymentResult, DeploymentTarget, Verification
from aura.cloud.manager import CloudManager
from aura.cloud.simulator import SimulatedCloudClient

__all__ = [
    "CloudManager",
    "CloudPolicy",
    "DeploymentResult",
    "DeploymentTarget",
    "SimulatedCloudClient",
    "Verification",
]