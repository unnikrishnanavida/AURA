from .schemas.api_response import ApiResponse
class PlanningApplication:
    def __init__(self, planner=None, replanner=None, simulator=None):
        self.planner, self.replanner, self.simulator = planner, replanner, simulator
    def plan(self, request):
        request.validate()
        if self.planner is None: raise RuntimeError("planner service is not configured")
        return ApiResponse.ok(self.planner.plan(request), request.request_id)
    def replan(self, request):
        request.validate()
        if self.replanner is None: raise RuntimeError("replanner service is not configured")
        return ApiResponse.ok(self.replanner.replan(request), request.request_id)
    def simulate(self, request):
        request.validate()
        if self.simulator is None: raise RuntimeError("simulator service is not configured")
        return ApiResponse.ok(self.simulator.simulate(request), None)
