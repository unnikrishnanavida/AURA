class CapabilityBroker:
 def __init__(self,granted=()): self.granted=set(granted)
 def require(self,x):
  if x not in self.granted: raise PermissionError(f"capability denied: {x}")
