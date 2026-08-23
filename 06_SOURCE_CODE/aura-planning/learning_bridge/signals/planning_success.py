from dataclasses import dataclass
@dataclass(frozen=True,slots=True)
class PlanningSuccess:
    plan_id:str; quality:float; strategy:str
