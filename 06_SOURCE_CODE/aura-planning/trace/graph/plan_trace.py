class PlanTrace:
    def __init__(self):
        self.nodes={}; self.edges=[]
    def add_node(self,node): self.nodes[node.node_id]=node
    def add_edge(self,edge):
        if edge.source not in self.nodes or edge.target not in self.nodes: raise KeyError("trace nodes must exist")
        self.edges.append(edge)
    def subgraph(self,node_ids):
        ids=set(node_ids)
        return tuple(e for e in self.edges if e.source in ids and e.target in ids)
