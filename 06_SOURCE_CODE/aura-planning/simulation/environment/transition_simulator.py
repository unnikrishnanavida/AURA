class TransitionSimulator:
    def apply(self,state,action):
        outcome=action.apply(state)
        return outcome
