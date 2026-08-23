class DependencyAnalyzer:
    def parallel_groups(self,graph):
        order=graph.topological_order()
        completed=set()
        groups=[]
        remaining=set(order)
        while remaining:
            ready=[n for n in remaining if set(graph.predecessors(n))<=completed]
            if not ready: raise ValueError("dependency cycle detected")
            groups.append(tuple(sorted(ready)))
            completed.update(ready); remaining.difference_update(ready)
        return tuple(groups)

    def blocking_nodes(self,graph):
        return {n:len(graph.successors(n)) for n in graph.nodes}
