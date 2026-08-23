class CapabilityRegistry:
    def __init__(self): self._items={}
    def register(self, capability): self._items[capability.name]=capability
    def get(self,name): return self._items.get(name)
    def remove(self,name): return self._items.pop(name,None)
    def all(self): return tuple(self._items.values())
