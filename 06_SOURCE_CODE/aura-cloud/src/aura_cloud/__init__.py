"""aura-cloud — cloud abstraction for AURA.

Provides provider protocols, deployment contracts, cost budgets, rollback,
and deployment audit. No real AWS/Azure/GCP deployment is claimed: providers
are interfaces, and the bundled provider is explicitly a SIMULATED provider.
"""

__version__ = "0.2.0"

from aura_cloud.deployment.rollback import RollbackLedger, RollbackRecord
from aura_cloud.engine import CloudControlPlane
from aura_cloud.finops.budget import CostBudget, CostEstimate
from aura_cloud.ledger.change_events import ChangeEvent, DeploymentAudit
from aura_cloud.models import CloudIntent, DeploymentPlan, DeploymentState
from aura_cloud.providers.contracts import (
    BaseCloudProvider,
    CloudProvider,
    DeploymentResult,
)
from aura_cloud.providers.simulator import SimulatedProvider

__all__ = [
    "BaseCloudProvider",
    "ChangeEvent",
    "CloudControlPlane",
    "CloudIntent",
    "CloudProvider",
    "CostBudget",
    "CostEstimate",
    "DeploymentAudit",
    "DeploymentPlan",
    "DeploymentResult",
    "DeploymentState",
    "RollbackLedger",
    "RollbackRecord",
    "SimulatedProvider",
]
