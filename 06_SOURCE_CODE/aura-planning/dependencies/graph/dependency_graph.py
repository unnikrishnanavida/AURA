from collections import defaultdict, deque

class DependencyGraph:
    def __init__(self):
        self.nodes={}
        self.edges=defaultdict(set)
        self.reverse=defaultdict(set)

    def add_node(self,node):
        if node.node_id in self.nodes: raise ValueError(f"duplicate node: {node.node_id}")
        self.nodes[node.node_id]=node

    def add_edge(self,edge):
        if edge.source not in self.nodes or edge.target not in self.nodes:
            raise KeyError("both dependency nodes must exist")
        self.edges[edge.source].add(edge.target)
        self.reverse[edge.target].add(edge.source)

    def predecessors(self,node_id): return tuple(self.reverse[node_id])
    def successors(self,node_id): return tuple(self.edges[node_id])

    def topological_order(self):
        indegree={n:len(self.reverse[n]) for n in self.nodes}
        queue=deque(n for n,d in indegree.items() if d==0)
        order=[]
        while queue:
            node=queue.popleft(); order.append(node)
            for child in self.edges[node]:
                indegree[child]-=1
                if indegree[child]==0: queue.append(child)
        if len(order)!=len(self.nodes): raise ValueError("dependency graph contains a cycle")
        return order
