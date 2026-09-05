from dataclasses import dataclass, field
from enum import Enum


class DeploymentState(str,Enum): PLANNED="planned"; APPROVED="approved"; DEPLOYED="deployed"; ROLLED_BACK="rolled_back"
@dataclass(frozen=True)
class CloudIntent: workload:str; region:str; capabilities:tuple[str,...]=()
@dataclass(frozen=True)
class DeploymentPlan: plan_id:str; provider:str; changes:tuple[str,...]; risk:float; state:DeploymentState=DeploymentState.PLANNED; metadata:dict=field(default_factory=dict)
