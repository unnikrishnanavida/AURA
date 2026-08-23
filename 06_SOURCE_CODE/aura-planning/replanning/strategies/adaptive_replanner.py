class AdaptiveReplanner:
    def __init__(self,full,partial): self.full,self.partial=full,partial
    def replan(self,request,planner,stable_prefix=()):
        return self.partial.replan(request,planner,stable_prefix) if stable_prefix else self.full.replan(request,planner)
