class BackwardPlanner:
    def __init__(self,actions=()): self.actions=tuple(actions)
    def relevant(self,goal):
        target=set(getattr(goal,"values",getattr(goal,"desired_state",{})).keys())
        return tuple(a for a in self.actions if any(getattr(e,"variable",None) in target for e in a.effects))
