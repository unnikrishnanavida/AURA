class CapabilityPolicy:
 def __init__(self,allowed=()):self.allowed=set(allowed)
 def authorize(self,a):
  if a.capability not in self.allowed:raise PermissionError(a.capability)
