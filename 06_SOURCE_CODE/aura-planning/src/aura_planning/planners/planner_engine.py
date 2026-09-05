class PlannerEngine:
    def __init__(self, planners):
        self.planners=dict(planners)
    def plan(self, strategy, *args, **kwargs):
        planner=self.planners.get(strategy)
        if planner is None: raise KeyError(f"planner unavailable: {strategy}")
        return planner.plan(*args,**kwargs)
