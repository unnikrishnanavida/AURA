class PlannerRouter:
    def __init__(self): self._planners={}
    def register(self,name,planner): self._planners[name]=planner
    def route(self,name): return self._planners[name]
