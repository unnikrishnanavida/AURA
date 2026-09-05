from dataclasses import dataclass,field
@dataclass(slots=True)
class Schedule:
    starts:dict[str,float]=field(default_factory=dict); durations:dict[str,float]=field(default_factory=dict)
    def finish(self,i): return self.starts[i]+self.durations[i]
    def makespan(self): return max((self.finish(i) for i in self.starts),default=0)
    def overlaps(self,a,b): return self.starts[a]<self.finish(b) and self.starts[b]<self.finish(a)
