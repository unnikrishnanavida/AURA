from dataclasses import dataclass
@dataclass(frozen=True)
class ExecutionSnapshot:
    execution_id:str
    status:str
    state:dict
