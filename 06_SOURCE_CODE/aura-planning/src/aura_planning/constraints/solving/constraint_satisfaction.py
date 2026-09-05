class ConstraintSatisfaction:
    def find(self, candidates, constraints):
        return next((candidate for candidate in candidates if not constraints.validate(candidate)),None)
    def all(self,candidates,constraints):
        return tuple(c for c in candidates if not constraints.validate(c))
