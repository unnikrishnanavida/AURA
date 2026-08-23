from dataclasses import dataclass
@dataclass(frozen=True)
class ExecutionFailure:
    error:str
    transient:bool=False
    timeout:bool=False
    policy:bool=False
    resource:bool=False
