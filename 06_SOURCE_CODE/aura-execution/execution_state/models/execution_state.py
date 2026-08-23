from dataclasses import dataclass, field
from aura_execution.contracts.responses.execution_status import ExecutionStatus
@dataclass
class ExecutionState:
    status: ExecutionStatus = ExecutionStatus.PENDING
    attempt: int = 0
    data: dict = field(default_factory=dict)
    error: str | None = None
