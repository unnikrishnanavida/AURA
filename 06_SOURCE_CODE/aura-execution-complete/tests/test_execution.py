from aura_execution.engine import ExecutionEngine
from aura_execution.models import Action,Status
def test_execution():assert ExecutionEngine(('echo',)).execute([Action('1','echo')],lambda a:'ok').status is Status.SUCCEEDED
