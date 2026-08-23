from aura_execution.actions.preparation.precondition_validator import check_preconditions
class PreconditionChecker:
    def check(self,action,state,inputs): return check_preconditions(action,state,inputs)
