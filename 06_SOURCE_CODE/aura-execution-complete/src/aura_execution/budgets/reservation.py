from dataclasses import dataclass
@dataclass
class Budget:
 limit:int; used:int=0
 def reserve(self,n):
  if n<0 or self.used+n>self.limit: return False
  self.used+=n; return True
