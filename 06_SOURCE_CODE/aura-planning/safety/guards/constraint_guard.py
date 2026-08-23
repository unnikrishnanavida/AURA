class ConstraintGuard:
    def allow(self, plan, constraints):
        return not tuple(constraints.validate(plan))
