from dataclasses import dataclass
@dataclass(frozen=True)
class ExecutionSuccess:
    action_id:str
    duration:float
