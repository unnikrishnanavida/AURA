class Orchestrator:
    def __init__(self,planning_pipeline=None,evaluation_pipeline=None):
        self.planning=planning_pipeline; self.evaluation=evaluation_pipeline
    def plan(self,request):
        if self.planning is None: raise RuntimeError("planning pipeline unavailable")
        plan=self.planning.run(request)
        return {"plan":plan,"evaluation":self.evaluation.run(plan) if self.evaluation else None}
