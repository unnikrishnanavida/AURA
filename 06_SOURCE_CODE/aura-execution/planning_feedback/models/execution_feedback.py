from dataclasses import dataclass
@dataclass(frozen=True)
class ExecutionFeedback:
    plan_id:str
    success:bool
    deviation:dict
