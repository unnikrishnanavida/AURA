from dataclasses import dataclass,field
@dataclass(frozen=True,slots=True)
class SimulationRequest:
    planning:object; horizon:int=1; scenarios:tuple=(); options:dict=field(default_factory=dict)
    def validate(self):
        self.planning.validate()
        if self.horizon<=0: raise ValueError("horizon must be positive")
