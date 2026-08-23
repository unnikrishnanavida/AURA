from dataclasses import dataclass
@dataclass(frozen=True,slots=True)
class PlanningFailure:
    plan_id:str; reason:str; strategy:str
