class RetrievalRegistry:
    def __init__(self): self._items={}
    def register(self,name,adapter):
        if name in self._items: raise ValueError("duplicate adapter")
        self._items[name]=adapter
    def names(self): return tuple(sorted(self._items))
