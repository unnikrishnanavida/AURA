class DependencyResolver:
    def resolve_ready(self,graph,completed):
        return [i for i,n in graph.nodes.items() if n.ready(completed)]
    def closure(self,graph,targets):
        required=set(targets); stack=list(targets)
        while stack:
            i=stack.pop()
            for p in graph.nodes[i].incoming:
                if p not in required: required.add(p); stack.append(p)
        return required
