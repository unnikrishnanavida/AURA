from dataclasses import dataclass
@dataclass(frozen=True)
class ExecutionFailureSignal:
    action_id:str
    reason:str
