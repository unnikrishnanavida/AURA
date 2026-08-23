from dataclasses import dataclass
from .planning_state import PlanningState
@dataclass(frozen=True,slots=True)
class WorldState:
    planning:PlanningState; world_version:int=0
    def evolve(self,updates): return WorldState(self.planning.with_updates(updates),self.world_version+1)
