class ResourceChecker:
    def feasible(self, requirements, registry):
        try:
            from .resource_allocator import ResourceAllocator
            ResourceAllocator().allocate(requirements, registry)
            return True
        except (KeyError, ValueError):
            return False
