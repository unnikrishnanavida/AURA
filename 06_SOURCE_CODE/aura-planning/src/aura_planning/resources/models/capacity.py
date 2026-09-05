from dataclasses import dataclass
@dataclass(frozen=True,slots=True)
class Capacity:
    limit:float
    used:float=0.0
    @property
    def available(self): return max(0.0,self.limit-self.used)
    def allocate(self,amount):
        if amount<0 or amount>self.available: raise ValueError("capacity exceeded")
        return Capacity(self.limit,self.used+amount)
