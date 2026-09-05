from dataclasses import dataclass,field
@dataclass(frozen=True,slots=True)
class WorldQuery:
    entity:str
    attributes:tuple=()
    metadata:dict=field(default_factory=dict)
