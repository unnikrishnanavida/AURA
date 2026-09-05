from .forward_planner import ForwardPlanner
class StateSpacePlanner(ForwardPlanner):
    def plan_path(self,initial,goal):
        result=self.plan(initial,goal)
        return result.node.path() if result.success else None
