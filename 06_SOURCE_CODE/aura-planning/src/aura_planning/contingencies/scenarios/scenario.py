from dataclasses import dataclass,field
@dataclass(frozen=True,slots=True)
class Scenario:
    name:str
    probability:float
    changes:dict=field(default_factory=dict)
    def __post_init__(self):
        if not 0<=self.probability<=1: raise ValueError("probability must be [0,1]")
