from dataclasses import dataclass, field


@dataclass
class ResourceBudget:
    limits:dict[str,float]=field(default_factory=dict)
    used:dict[str,float]=field(default_factory=dict)
    def consume(self,name,amount):
        new=self.used.get(name,0)+amount
        if new>self.limits.get(name,float("inf")): return False
        self.used[name]=new; return True
