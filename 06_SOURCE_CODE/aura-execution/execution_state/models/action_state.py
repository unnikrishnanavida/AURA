from dataclasses import dataclass
from aura_execution.contracts.responses.execution_status import ExecutionStatus
@dataclass
class ActionState:
    action_id: str
    status: ExecutionStatus=ExecutionStatus.PENDING
    attempts: int=0
