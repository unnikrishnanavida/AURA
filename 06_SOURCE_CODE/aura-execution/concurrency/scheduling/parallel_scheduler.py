def parallel_groups(dependencies):
    remaining={k:set(v) for k,v in dependencies.items()};groups=[]
    while remaining:
        ready=sorted(k for k,v in remaining.items() if not v)
        if not ready:raise ValueError("cyclic dependency")
        groups.append(ready)
        for k in ready:remaining.pop(k)
        for deps in remaining.values():deps.difference_update(ready)
    return groups
