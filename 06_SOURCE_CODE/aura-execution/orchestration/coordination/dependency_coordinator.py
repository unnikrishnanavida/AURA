class DependencyCoordinator:
    def order(self,dependencies):
        pending={k:set(v) for k,v in dependencies.items()};order=[]
        while pending:
            ready=[k for k,v in pending.items() if not v]
            if not ready:raise ValueError("cyclic execution dependency")
            order.extend(sorted(ready))
            for k in ready:pending.pop(k)
            for v in pending.values():v.difference_update(ready)
        return order
