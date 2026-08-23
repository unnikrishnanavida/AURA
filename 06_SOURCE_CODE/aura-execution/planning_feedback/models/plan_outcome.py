from dataclasses import dataclass
@dataclass(frozen=True)
class PlanOutcome:
    plan_id:str
    success:bool
    score:float
