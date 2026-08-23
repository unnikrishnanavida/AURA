class PlanningCoordinator:
    def __init__(self,router): self.router=router
    def execute(self,planner_name,request): return self.router.route(planner_name).plan(request)
