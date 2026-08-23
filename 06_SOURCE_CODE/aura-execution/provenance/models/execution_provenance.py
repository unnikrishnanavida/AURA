from dataclasses import dataclass
@dataclass(frozen=True)
class ExecutionProvenance:
    execution_id:str
    parent_id:str|None=None
    source:str="unknown"
