from dataclasses import dataclass
@dataclass(frozen=True,slots=True)
class ExecutionPlan:
    plan_id:str
    actions:tuple
    preconditions:tuple=()
    metadata:dict=None
    def __post_init__(self):
        if not self.plan_id: raise ValueError("plan_id is required")
