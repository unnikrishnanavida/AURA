from dataclasses import dataclass
@dataclass(frozen=True)
class ExecutionEvent:
    name:str
    execution_id:str
    data:dict
