import pytest
from aura_execution.execution_state.state_engine import StateEngine
from aura_execution.contracts.responses.execution_status import ExecutionStatus
def test_lifecycle():
    s=StateEngine();s.move(ExecutionStatus.READY);s.move(ExecutionStatus.RUNNING);s.move(ExecutionStatus.SUCCEEDED)
    assert s.state.status==ExecutionStatus.SUCCEEDED
def test_invalid_transition():
    s=StateEngine()
    with pytest.raises(Exception):s.move(ExecutionStatus.SUCCEEDED)
