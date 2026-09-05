class ResourceAllocator:
    def allocate(self, requirements, registry):
        used = {}
        for req in requirements:
            resource = registry.get(req.resource)
            next_amount = used.get(req.resource, 0) + req.amount
            if next_amount > resource.capacity:
                raise ValueError(f"insufficient resource: {req.resource}")
            used[req.resource] = next_amount
        return used
