from dataclasses import dataclass, field
from .execution_status import ExecutionStatus
@dataclass
class ExecutionResult:
    execution_id: str
    status: ExecutionStatus
    action_result: object | None = None
    reason: str | None = None
    events: list[dict] = field(default_factory=list)
