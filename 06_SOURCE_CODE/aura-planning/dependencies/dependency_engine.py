from .analysis.dependency_analyzer import DependencyAnalyzer
from .analysis.critical_path import CriticalPath
class DependencyEngine:
    def __init__(self,graph):
        self.graph=graph; self.analyzer=DependencyAnalyzer(); self.critical=CriticalPath()
    def order(self): return self.graph.topological_order()
    def parallel_groups(self): return self.analyzer.parallel_groups(self.graph)
    def critical_path(self,durations): return self.critical.calculate(self.graph,durations)
