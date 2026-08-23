class ReactivePlanner:
    def __init__(self, policies=()): self.policies=tuple(policies)
    def respond(self,state):
        for policy in self.policies:
            action=policy.select(state)
            if action is not None: return action
        return None
