class ToolResolver:
    def __init__(self,registry): self.registry=registry
    def for_capability(self,capability):
        return [t for t in self.registry._tools.values() if t.capability==capability]
