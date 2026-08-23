from aura_execution.contracts.responses.execution_status import ExecutionStatus
from .models.execution_state import ExecutionState
from .transitions.transition_manager import transition
class StateEngine:
    def __init__(self): self.state=ExecutionState()
    def move(self,target): return transition(self.state,target)
    def reset(self): self.state=ExecutionState(); return self.state
    def snapshot(self): return {"status":self.state.status.value,"attempt":self.state.attempt,"data":dict(self.state.data),"error":self.state.error}
