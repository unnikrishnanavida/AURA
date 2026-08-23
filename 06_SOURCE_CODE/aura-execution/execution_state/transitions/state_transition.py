from dataclasses import dataclass
from aura_execution.contracts.responses.execution_status import ExecutionStatus
@dataclass(frozen=True)
class StateTransition:
    source: ExecutionStatus
    target: ExecutionStatus
