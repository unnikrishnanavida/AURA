from .conversion.plan_converter import convert_plan
class PlanningAdapter:
    def __init__(self,planner):self.planner=planner
    def to_execution_actions(self,plan,handlers=None):return convert_plan(plan,handlers)
