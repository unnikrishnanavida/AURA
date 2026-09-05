from uuid import uuid4

from .control_plane.capabilities import require
from .models import DeploymentPlan
from .policy.guardrails import allow_plan


class CloudControlPlane:
 def __init__(self,provider,risk_budget=.5): self.provider=provider; self.risk_budget=risk_budget
 def plan(self,intent,risk=.1):
  require(self.provider,intent.capabilities)
  if not allow_plan(risk,self.risk_budget): raise PermissionError("deployment rejected")
  self.provider.plan(intent)
  return DeploymentPlan(str(uuid4()),self.provider.name,(f"deploy:{intent.workload}",),risk)
