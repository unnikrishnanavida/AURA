from dataclasses import dataclass
@dataclass(frozen=True,slots=True)
class WorldObservation:
    entity:str
    values:dict
    timestamp:float
    source:str
