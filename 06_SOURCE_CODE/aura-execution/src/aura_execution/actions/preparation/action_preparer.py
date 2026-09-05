from .input_resolver import resolve_inputs
from .precondition_validator import check_preconditions


class ActionPreparer:
    def prepare(self,action,state,inputs):
        resolved=resolve_inputs(action,inputs) if action.inputs else dict(inputs)
        failures=check_preconditions(action,state,resolved)
        if failures: raise ValueError(f"preconditions failed: {failures}")
        return resolved
