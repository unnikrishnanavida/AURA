class ProvenanceEngine:
    def __init__(self,graph):self.graph=graph
    def lineage(self,node_id):
        result=[];seen=set();stack=[node_id]
        while stack:
            n=stack.pop()
            if n in seen:continue
            seen.add(n);result.append(n);stack.extend(self.graph.parents(n))
        return result
