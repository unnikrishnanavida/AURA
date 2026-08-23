class CriticalPath:
    def calculate(self, graph, durations):
        order=graph.topological_order()
        distance={node:0.0 for node in order}
        parent={}
        for node in order:
            for child in graph.successors(node):
                candidate=distance[node]+float(durations.get(node,0))
                if candidate>distance[child]:
                    distance[child]=candidate; parent[child]=node
        if not distance: return ()
        end=max(distance,key=distance.get)
        path=[end]
        while end in parent:
            end=parent[end]; path.append(end)
        return tuple(reversed(path))
