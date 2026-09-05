from uuid import uuid4
from .models import ExecutionRecord,Status
from .policy.capabilities import CapabilityPolicy
from .policy.budgets import ActionBudget
from .runtime.cancellation import CancellationToken
from .observability.ledger import ExecutionLedger
class ExecutionEngine:
 def __init__(self,capabilities=(),max_actions=100):self.policy=CapabilityPolicy(capabilities);self.budget=ActionBudget(max_actions)
 def execute(self,actions,runner,token=None):
  token=token or CancellationToken();record=ExecutionRecord(str(uuid4()),Status.RUNNING,list(actions));ledger=ExecutionLedger()
  try:
   for a in actions:
    token.check();self.policy.authorize(a);self.budget.consume();result=runner(a);ledger.append({'action':a.action_id,'result':result});record.events.append(ledger.events[-1])
   record.status=Status.SUCCEEDED
  except Exception as exc:
   record.status=Status.CANCELLED if token.cancelled else Status.FAILED;record.events.append({'error':str(exc)})
  return record
