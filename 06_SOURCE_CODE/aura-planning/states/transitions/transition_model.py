class TransitionModel:
    def __init__(self, actions=()):
        self.actions = list(actions)

    def successors(self, state):
        for action in self.actions:
            if action.is_applicable(state):
                outcome = action.apply(state)
                if outcome.success:
                    yield action, outcome.state
