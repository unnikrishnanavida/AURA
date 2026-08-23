from dataclasses import dataclass
import time
@dataclass(frozen=True,slots=True)
class PlanSnapshot:
    plan_id:str; actions:tuple; created_at:float
    @classmethod
    def capture(cls,plan_id,plan): return cls(plan_id,tuple(getattr(plan,"actions",plan)),time.time())
