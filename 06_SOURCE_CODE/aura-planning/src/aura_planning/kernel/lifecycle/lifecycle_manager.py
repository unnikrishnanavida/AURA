from __future__ import annotations
from dataclasses import dataclass
from .bootstrap import bootstrap
from .health import HealthReport,check_runtime
from .shutdown import shutdown
from ..identity.planning_identity import PlanningIdentity
from ..runtime.runtime import PlanningRuntime

@dataclass(slots=True)
class LifecycleManager:
    runtime:PlanningRuntime|None=None
    identity:PlanningIdentity|None=None
    def start(self,request:object,planner_version:str="1.0")->PlanningIdentity:
        if self.runtime is not None: raise RuntimeError("already started")
        self.runtime,self.identity=bootstrap(request,planner_version); return self.identity
    def health(self)->HealthReport:
        return check_runtime(self.runtime) if self.runtime else HealthReport(False,"created",{"runtime":False},{})
    def stop(self)->None:
        if self.runtime: shutdown(self.runtime)
