class CapabilityResolver:
    def __init__(self, registry): self.registry=registry
    def resolve(self, name, operation):
        c=self.registry.get(name)
        return c if c and c.supports(operation) else None
