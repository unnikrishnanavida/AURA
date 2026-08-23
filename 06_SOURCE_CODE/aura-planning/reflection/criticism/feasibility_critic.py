class FeasibilityCritic:
    def critique(self,plan,constraints):
        return tuple(constraints.validate(plan))
