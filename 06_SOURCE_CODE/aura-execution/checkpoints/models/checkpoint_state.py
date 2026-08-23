from dataclasses import dataclass
@dataclass(frozen=True)
class CheckpointState:
    status:str
    state:dict
