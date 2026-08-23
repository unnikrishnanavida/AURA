class RollbackStrategy:
    def choose(self,action):return action.reversible
