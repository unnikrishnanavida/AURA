class NegotiationEngine:
    def __init__(self,goal_negotiator,resource_negotiator):
        self.goals=goal_negotiator; self.resources=resource_negotiator
    def resolve_goals(self,goals): return self.goals.resolve(goals)
    def allocate(self,requests,capacity): return self.resources.negotiate(requests,capacity)
