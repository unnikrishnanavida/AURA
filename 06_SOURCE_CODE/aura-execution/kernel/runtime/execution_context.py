from dataclasses import dataclass,field
@dataclass
class ExecutionContext:
    execution_id:str
    principal:str="system"
    state:dict=field(default_factory=dict)
    scopes:set[str]=field(default_factory=lambda:{"*"})
    approved:bool=False
