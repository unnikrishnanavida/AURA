import time
from aura_execution.kernel.identity.execution_id import ExecutionId
from aura_execution.contracts.responses.execution_status import ExecutionStatus
from aura_execution.contracts.responses.execution_result import ExecutionResult
from aura_execution.kernel.runtime.execution_context import ExecutionContext
from aura_execution.execution_state.state_engine import StateEngine
from aura_execution.actions.preparation.action_preparer import ActionPreparer
from aura_execution.capabilities.registry.capability_registry import CapabilityRegistry
from aura_execution.permissions.policies.permission_policy import PermissionPolicy
from aura_execution.permissions.policies.resource_policy import ResourcePolicy
from aura_execution.permissions.approval.approval_manager import ApprovalManager
from aura_execution.permissions.permission_engine import PermissionEngine
from aura_execution.safety.safety_engine import SafetyEngine
from aura_execution.budgets.budget_engine import BudgetEngine
from aura_execution.actions.action_engine import ActionEngine
from aura_execution.validation.validation_engine import ValidationEngine
from aura_execution.observation.observation_engine import ObservationEngine
from aura_execution.recovery.recovery_engine import RecoveryEngine
from aura_execution.flight_recorder.flight_recorder import FlightRecorder

class Orchestrator:
    def __init__(self, capability_engine, permission_engine, safety_engine, budget_engine, action_engine, validator, observer, recovery, recorder):
        self.capabilities=capability_engine;self.permissions=permission_engine;self.safety=safety_engine
        self.budget=budget_engine;self.actions=action_engine;self.validator=validator;self.observer=observer
        self.recovery=recovery;self.recorder=recorder;self.preparer=ActionPreparer()

    @classmethod
    def default(cls):
        from aura_execution.capabilities.capability_engine import CapabilityEngine
        registry=CapabilityRegistry()
        return cls(CapabilityEngine(registry),
                   PermissionEngine(PermissionPolicy({("system","execute"):"allow"}),ResourcePolicy(),ApprovalManager()),
                   SafetyEngine(),BudgetEngine(),ActionEngine(),ValidationEngine(),ObservationEngine(),RecoveryEngine(),FlightRecorder())

    def register_capability(self,capability): self.capabilities.registry.register(capability)

    def execute(self,request,principal="system"):
        eid=str(ExecutionId.new());state_engine=StateEngine();self.recorder.record(eid,"received")
        action=request.action
        context=ExecutionContext(eid,principal,dict(request.state),{"*"},request.approved)
        try:
            state_engine.move(ExecutionStatus.READY)
            if not self.capabilities.check(action.capability, action.name):
                state_engine.move(ExecutionStatus.BLOCKED);self.recorder.record(eid,"capability.denied")
                return ExecutionResult(eid,ExecutionStatus.BLOCKED,reason="required capability unavailable")
            permission=self.permissions.authorize(principal,action,context)
            if permission=="deny":
                state_engine.move(ExecutionStatus.DENIED);return ExecutionResult(eid,ExecutionStatus.DENIED,reason="permission denied")
            if permission=="review":
                state_engine.move(ExecutionStatus.REVIEW);return ExecutionResult(eid,ExecutionStatus.REVIEW,reason="approval required")
            safety=self.safety.evaluate(action,request.approved)
            if safety.decision=="DENY":
                state_engine.move(ExecutionStatus.DENIED);return ExecutionResult(eid,ExecutionStatus.DENIED,reason="safety policy denied")
            if safety.decision=="REVIEW":
                state_engine.move(ExecutionStatus.REVIEW);return ExecutionResult(eid,ExecutionStatus.REVIEW,reason="safety approval required")
            if not self.budget.check():
                state_engine.move(ExecutionStatus.BLOCKED);return ExecutionResult(eid,ExecutionStatus.BLOCKED,reason="budget exhausted")
            inputs=self.preparer.prepare(action,context.state,request.inputs)
            state_engine.move(ExecutionStatus.RUNNING);self.recorder.record(eid,"running",action_id=action.action_id)
            started=time.monotonic()
            dispatch=self.actions.execute(action,inputs,context)
            duration=time.monotonic()-started
            self.budget.record(duration=duration)
            if not dispatch.success:
                state_engine.move(ExecutionStatus.FAILED)
                strategy=self.recovery.recommend(dispatch.error,1,action.max_retries,action.reversible,False)
                self.recorder.record(eid,"failed",error=dispatch.error,recovery=strategy)
                return ExecutionResult(eid,ExecutionStatus.FAILED,reason=dispatch.error)
            before=dict(context.state)
            after=dict(context.state);after.update(action.effects)
            observation=self.observer.observe(before,after)
            from aura_execution.contracts.responses.action_result import ActionResult
            ar=ActionResult(True,dispatch.value,None,duration,{"changes":observation.changes})
            ok,details=self.validator.validate(ar,action.effects,after)
            if not ok:
                state_engine.move(ExecutionStatus.FAILED);return ExecutionResult(eid,ExecutionStatus.FAILED,ar,"expected state mismatch")
            context.state=after;state_engine.move(ExecutionStatus.SUCCEEDED)
            self.recorder.record(eid,"completed",duration=duration)
            return ExecutionResult(eid,ExecutionStatus.SUCCEEDED,ar,events=[e.as_dict() for e in self.recorder.for_execution(eid)])
        except Exception as exc:
            if state_engine.state.status in {ExecutionStatus.RUNNING,ExecutionStatus.READY}: state_engine.move(ExecutionStatus.FAILED)
            self.recorder.record(eid,"exception",error=str(exc))
            return ExecutionResult(eid,ExecutionStatus.FAILED,reason=str(exc))
