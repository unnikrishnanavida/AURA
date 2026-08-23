from dataclasses import dataclass
@dataclass(frozen=True,slots=True)
class PlanningFeedback:
    plan_id:str; reward:float; metadata:dict
