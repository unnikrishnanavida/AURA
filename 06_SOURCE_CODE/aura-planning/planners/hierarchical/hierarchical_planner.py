from .decomposition_planner import DecompositionPlanner
class HierarchicalPlanner:
    def __init__(self,rules): self.decomposer=DecompositionPlanner(rules)
    def plan(self,root_task):
        return tuple(task.action for task in self.decomposer.decompose(root_task) if task.action is not None)
