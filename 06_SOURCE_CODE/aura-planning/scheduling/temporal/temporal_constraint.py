from dataclasses import dataclass
@dataclass(frozen=True,slots=True)
class TemporalConstraint:
    before:str; after:str; minimum_gap:float=0
    def satisfied(self,finish_times): return finish_times.get(self.before,0)+self.minimum_gap<=finish_times.get(self.after,float("inf"))
