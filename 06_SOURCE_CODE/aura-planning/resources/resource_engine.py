from .allocation.resource_allocator import ResourceAllocator
from .allocation.resource_checker import ResourceChecker
class ResourceEngine:
    def __init__(self, registry):
        self.registry = registry
        self.allocator = ResourceAllocator()
        self.checker = ResourceChecker()
    def feasible(self, requirements):
        return self.checker.feasible(requirements, self.registry)
    def allocate(self, requirements):
        return self.allocator.allocate(requirements, self.registry)
