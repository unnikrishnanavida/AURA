class PermissionBroker:
 def __init__(self,granted=()):self.granted=set(granted)
 def require(self,p):
  if p not in self.granted:raise PermissionError(p)
