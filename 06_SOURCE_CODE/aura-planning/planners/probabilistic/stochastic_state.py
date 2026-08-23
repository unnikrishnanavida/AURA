from dataclasses import dataclass
@dataclass(frozen=True,slots=True)
class StochasticState:
    state:object; probability:float
    def __post_init__(self):
        if not 0<=self.probability<=1: raise ValueError("probability outside [0,1]")
