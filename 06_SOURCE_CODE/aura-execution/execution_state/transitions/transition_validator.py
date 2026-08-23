from aura_execution.contracts.responses.execution_status import ExecutionStatus
_ALLOWED={
ExecutionStatus.PENDING:{ExecutionStatus.READY,ExecutionStatus.CANCELLED},
ExecutionStatus.READY:{ExecutionStatus.RUNNING,ExecutionStatus.BLOCKED,ExecutionStatus.DENIED,ExecutionStatus.REVIEW},
ExecutionStatus.RUNNING:{ExecutionStatus.SUCCEEDED,ExecutionStatus.FAILED,ExecutionStatus.CANCELLED,ExecutionStatus.WAITING},
ExecutionStatus.WAITING:{ExecutionStatus.RUNNING,ExecutionStatus.CANCELLED},
ExecutionStatus.FAILED:{ExecutionStatus.RECOVERING,ExecutionStatus.CANCELLED},
ExecutionStatus.RECOVERING:{ExecutionStatus.RUNNING,ExecutionStatus.ROLLED_BACK,ExecutionStatus.FAILED},
ExecutionStatus.SUCCEEDED:set(), ExecutionStatus.BLOCKED:set(), ExecutionStatus.DENIED:set(),
ExecutionStatus.REVIEW:{ExecutionStatus.READY,ExecutionStatus.DENIED}, ExecutionStatus.CANCELLED:set(),
ExecutionStatus.ROLLED_BACK:set()
}
def can_transition(source,target): return target in _ALLOWED.get(source,set())
