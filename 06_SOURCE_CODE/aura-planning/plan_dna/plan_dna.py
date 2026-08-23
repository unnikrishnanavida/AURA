from dataclasses import dataclass
from .identity.plan_fingerprint import plan_fingerprint
from .lineage.plan_lineage import PlanLineage
@dataclass(slots=True)
class PlanDNA:
    plan_id:str
    fingerprint:str
    version:int
    lineage:PlanLineage
    @classmethod
    def create(cls,plan):
        fp=plan_fingerprint(plan); return cls(fp,fp,1,PlanLineage())
    def derive(self,plan,changes=()):
        child=PlanDNA.create(plan); child.version=self.version+1
        child.lineage.parent[child.plan_id]=self.plan_id
        child.lineage.changes[child.plan_id]=tuple(changes)
        return child
