from dataclasses import dataclass
from enum import Enum
class GoalStatus(str,Enum): PENDING="pending"; ACTIVE="active"; ACHIEVED="achieved"; BLOCKED="blocked"; FAILED="failed"
@dataclass(frozen=True,slots=True)
class GoalSchema:
    goal_id:str; description:str; priority:float=.5; deadline:float|None=None; status:GoalStatus=GoalStatus.PENDING; success_conditions:tuple[str,...]=()
    def validate(self):
        if not self.goal_id.strip() or not self.description.strip(): raise ValueError("goal identity and description required")
        if not 0<=self.priority<=1: raise ValueError("priority outside [0,1]")
        if not self.success_conditions: raise ValueError("success conditions required")
