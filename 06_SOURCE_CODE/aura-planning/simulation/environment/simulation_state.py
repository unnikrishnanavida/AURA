from dataclasses import dataclass,field
@dataclass(slots=True)
class SimulationState:
    values:dict=field(default_factory=dict)
    time:float=0.0
    def copy(self): return SimulationState(dict(self.values),self.time)
