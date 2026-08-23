from dataclasses import dataclass
@dataclass(frozen=True)
class PastExecution:
    action_id:str
    success:bool
    outcome:object
