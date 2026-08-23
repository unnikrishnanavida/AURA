from aura_execution.contracts.responses.execution_status import ExecutionStatus
from aura_execution.contracts.schemas.error_schema import StateTransitionError
from .transition_validator import can_transition
def transition(state,target):
    if not can_transition(state.status,target):
        raise StateTransitionError(f"{state.status.value} -> {target.value} is invalid")
    state.status=target
    return state
