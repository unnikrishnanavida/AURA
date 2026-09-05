class ResourceRegistry:
    def __init__(self, resources=()):
        self._resources = {}
        for resource in resources:
            self.register(resource)
    def register(self, resource):
        if resource.name in self._resources:
            raise ValueError(f"resource already registered: {resource.name}")
        self._resources[resource.name] = resource
    def get(self, name): return self._resources[name]
    def all(self): return tuple(self._resources.values())
