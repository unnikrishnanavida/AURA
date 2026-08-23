from tests.unit.test_vertical_slice import make
from aura_execution.contracts.requests.execution_request import ExecutionRequest
from aura_execution.contracts.responses.execution_status import ExecutionStatus
def test_pipeline_records_events():
    o,a=make();r=o.execute(ExecutionRequest(a,{"path":"x","text":"ok"}))
    assert r.status==ExecutionStatus.SUCCEEDED
    assert any(e["event"]=="completed" for e in r.events)
