from __future__ import annotations
from dataclasses import dataclass
from typing import Any
from ..runtime.runtime import PlanningRuntime
from ..runtime.runtime_state import RuntimePhase

@dataclass(frozen=True,slots=True)
class HealthReport:
    healthy:bool; phase:str; checks:dict[str,bool]; details:dict[str,Any]
    def as_dict(self)->dict[str,Any]: return {"healthy":self.healthy,"phase":self.phase,"checks":dict(self.checks),"details":dict(self.details)}

def check_runtime(runtime:PlanningRuntime)->HealthReport:
    checks={"context":runtime.context is not None,"state":runtime.state.phase!=RuntimePhase.FAILED,"resources":runtime.resources is not None}
    return HealthReport(all(checks.values()),runtime.state.phase.value,checks,{"counters":dict(runtime.state.counters)})
