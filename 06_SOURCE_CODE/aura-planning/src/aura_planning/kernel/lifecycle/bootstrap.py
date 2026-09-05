from __future__ import annotations
from ..identity.execution_id import ExecutionId
from ..identity.fingerprint import fingerprint
from ..identity.planning_identity import PlanningIdentity
from ..runtime.planning_context import PlanningContext
from ..runtime.runtime import PlanningRuntime

def bootstrap(request:object,planner_version:str="1.0")->tuple[PlanningRuntime,PlanningIdentity]:
    identity=PlanningIdentity(ExecutionId.create(),fingerprint(request),planner_version)
    runtime=PlanningRuntime()
    runtime.initialize(PlanningContext(str(identity.execution),{"request":request,"identity":identity}))
    return runtime,identity
