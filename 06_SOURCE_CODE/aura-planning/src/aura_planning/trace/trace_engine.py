from .graph.plan_trace import PlanTrace
from .graph.trace_node import TraceNode
from .graph.trace_edge import TraceEdge
class TraceEngine:
    def __init__(self):
        self.trace=PlanTrace(); self._counter=0
    def event(self,kind,payload=None,parent=None):
        self._counter+=1; node=TraceNode(str(self._counter),kind,payload); self.trace.add_node(node)
        if parent is not None: self.trace.add_edge(TraceEdge(str(parent),node.node_id,"causes"))
        return node.node_id
    def graph(self): return self.trace
