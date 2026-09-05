from dataclasses import dataclass
@dataclass(frozen=True,slots=True)
class PlanMemory:
    plan_id:str; goal_key:str; plan:object; outcome:float
