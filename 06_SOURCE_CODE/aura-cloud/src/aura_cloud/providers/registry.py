class ProviderRegistry:
 def __init__(self): self.items={}
 def register(self,p):
  if p.name in self.items: raise ValueError("duplicate provider")
  self.items[p.name]=p
 def get(self,name): return self.items[name]
