class PolicySelector:
    def __init__(self,policies=()): self.policies=tuple(policies)
    def select(self,state):
        applicable=[p for p in self.policies if p.matches(state)]
        return max(applicable,key=lambda p:getattr(p,"priority",0),default=None)
