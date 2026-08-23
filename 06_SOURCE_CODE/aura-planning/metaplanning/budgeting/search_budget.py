from dataclasses import dataclass
@dataclass(slots=True)
class SearchBudget:
    expansions:int=10000
    def allow(self): return self.expansions>0
    def consume(self,n=1): self.expansions-=n
