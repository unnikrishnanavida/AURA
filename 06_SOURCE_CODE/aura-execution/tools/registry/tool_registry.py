class ToolRegistry:
    def __init__(self): self._tools={}
    def register(self,tool): self._tools[tool.name]=tool
    def resolve(self,name):
        if name not in self._tools: raise KeyError(f"unknown tool: {name}")
        return self._tools[name]
    def names(self): return tuple(self._tools)
