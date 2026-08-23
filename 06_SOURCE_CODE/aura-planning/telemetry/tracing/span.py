from dataclasses import dataclass,field
import time,uuid
@dataclass(slots=True)
class Span:
    name:str
    span_id:str=field(default_factory=lambda:uuid.uuid4().hex)
    start:float=field(default_factory=time.perf_counter)
    end:float|None=None
    attributes:dict=field(default_factory=dict)
    def finish(self): self.end=time.perf_counter(); return self
    @property
    def duration(self): return (self.end or time.perf_counter())-self.start
