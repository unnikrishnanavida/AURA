from dataclasses import dataclass
@dataclass(frozen=True)
class ActionEvent:
    action_id:str
    phase:str
    success:bool
