from dataclasses import dataclass
@dataclass(frozen=True,slots=True)
class TimeWindow:
    start:float; end:float
    def __post_init__(self):
        if self.end<self.start: raise ValueError("invalid time window")
    def contains(self,t): return self.start<=t<=self.end
    def duration(self): return self.end-self.start
