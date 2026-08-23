from .analysis.deviation_analyzer import DeviationAnalyzer
from .strategies.partial_replanner import PartialReplanner
class ReplanningEngine:
    def __init__(self,planner):
        self.planner=planner; self.deviation=DeviationAnalyzer(); self.partial=PartialReplanner()
    def affected(self,expected,observed): return self.deviation.analyze(expected,observed)
    def replan(self,state,goal,stable_prefix=()):
        return self.partial.replan(state,goal,self.planner,stable_prefix)
