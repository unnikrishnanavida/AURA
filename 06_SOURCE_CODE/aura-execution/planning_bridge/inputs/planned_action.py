from dataclasses import dataclass
@dataclass(frozen=True)
class PlannedAction:
    action_id:str
    capability:str
    inputs:dict
