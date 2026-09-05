class ResourceManager:
    def __init__(self,resources=()):
        self.resources={r.name:r for r in resources}
    def register(self,resource):
        if resource.name in self.resources: raise ValueError(f"duplicate resource: {resource.name}")
        self.resources[resource.name]=resource
    def available(self,name):
        return self.resources[name].capacity
    def can_allocate(self,requirements):
        return all(self.resources[r.resource].capacity>=r.amount for r in requirements)
