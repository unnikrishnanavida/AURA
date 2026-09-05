from .planning.plan_merger import PlanMerger
class MultiAgentPlanner:
    def __init__(self,distributed): self.distributed=distributed; self.merger=PlanMerger()
    def plan(self,tasks): return self.merger.merge(self.distributed.plan(tasks))
