from aura_execution.orchestration.orchestrator import Orchestrator
from aura_execution.capabilities.models.capability import Capability
from aura_execution.actions.models.executable_action import ExecutableAction
from aura_execution.contracts.requests.execution_request import ExecutionRequest
from aura_execution.contracts.responses.execution_status import ExecutionStatus

def make():
    o=Orchestrator.default()
    o.register_capability(Capability("filesystem.write",frozenset({"write"})))
    a=ExecutableAction("write1","write","filesystem.write",inputs={"path","text"},effects={"file_created":True},
                       permissions=(),risk=.1,handler=lambda i,c: i["text"])
    return o,a

def test_success():
    o,a=make(); r=o.execute(ExecutionRequest(a,{"path":"x","text":"hello"},{"file_created":False}))
    assert r.status==ExecutionStatus.SUCCEEDED

def test_missing_capability():
    o=Orchestrator.default()
    a=ExecutableAction("x","x","database.delete",handler=lambda i,c:None)
    r=o.execute(ExecutionRequest(a))
    assert r.status==ExecutionStatus.BLOCKED

def test_high_risk_review():
    o,a=make(); a=ExecutableAction("r","r","filesystem.write",risk=.8,handler=lambda i,c:None)
    r=o.execute(ExecutionRequest(a,approved=False))
    assert r.status==ExecutionStatus.REVIEW

def test_expected_state_mismatch():
    o=Orchestrator.default();o.register_capability(Capability("x",frozenset({"x"})))
    a=ExecutableAction("x","x","x",effects={"ready":True},handler=lambda i,c:None)
    r=o.execute(ExecutionRequest(a,state={"ready":False}))
    assert r.status==ExecutionStatus.SUCCEEDED
