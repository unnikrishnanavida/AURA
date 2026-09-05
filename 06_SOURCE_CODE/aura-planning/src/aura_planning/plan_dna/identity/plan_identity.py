from dataclasses import dataclass
from .plan_fingerprint import plan_fingerprint
@dataclass(frozen=True,slots=True)
class PlanIdentity:
    plan_id:str; fingerprint:str
    @classmethod
    def create(cls,plan): return cls(plan_fingerprint(plan),plan_fingerprint(plan))
