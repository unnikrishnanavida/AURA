from __future__ import annotations
from dataclasses import dataclass
from threading import RLock

@dataclass(slots=True)
class ResourceLease:
    name:str; capacity:float; used:float=0.0
    @property
    def available(self)->float: return self.capacity-self.used

class ResourceManager:
    def __init__(self)->None:
        self._resources:dict[str,ResourceLease]={}; self._lock=RLock()
    def register(self,name:str,capacity:float)->None:
        if not name.strip() or capacity<0: raise ValueError("invalid resource registration")
        with self._lock:
            if name in self._resources: raise ValueError(f"resource exists: {name}")
            self._resources[name]=ResourceLease(name,float(capacity))
    def acquire(self,name:str,amount:float)->bool:
        if amount<0: raise ValueError("amount must be non-negative")
        with self._lock:
            lease=self._resources[name]
            if lease.available < amount: return False
            lease.used += amount; return True
    def release(self,name:str,amount:float)->None:
        if amount<0: raise ValueError("amount must be non-negative")
        with self._lock:
            lease=self._resources[name]; lease.used=max(0.0,lease.used-amount)
    def snapshot(self)->dict[str,dict[str,float]]:
        with self._lock:
            return {n:{"capacity":r.capacity,"used":r.used,"available":r.available} for n,r in self._resources.items()}
