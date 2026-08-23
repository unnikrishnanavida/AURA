from dataclasses import dataclass
@dataclass(frozen=True,slots=True)
class SimulationEvent:
    time: float
    name: str
    payload: object = None
