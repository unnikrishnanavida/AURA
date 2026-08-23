from dataclasses import dataclass
@dataclass(frozen=True)
class Checkpoint:
    id:str
    execution_id:str
    state:dict
