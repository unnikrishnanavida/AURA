class GoalNegotiator:
    def __init__(self,priority): self.priority=priority
    def resolve(self,goals):
        return self.priority.negotiate(*goals[:2]) if len(goals)>=2 else (goals[0] if goals else None)
