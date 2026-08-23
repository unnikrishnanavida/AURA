from dataclasses import dataclass, field
@dataclass
class WorkflowState:
    current: str="pending"
    completed: list[str]=field(default_factory=list)
    failed: list[str]=field(default_factory=list)
