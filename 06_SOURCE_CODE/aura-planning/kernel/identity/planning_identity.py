from __future__ import annotations
from dataclasses import dataclass
from .execution_id import ExecutionId
from .fingerprint import fingerprint

@dataclass(frozen=True,slots=True)
class PlanningIdentity:
    execution:ExecutionId; request_fingerprint:str; planner_version:str
    def matches_request(self,request:object)->bool: return self.request_fingerprint==fingerprint(request)
    def as_dict(self)->dict[str,str]:
        return {"execution_id":str(self.execution),"request_fingerprint":self.request_fingerprint,"planner_version":self.planner_version}
