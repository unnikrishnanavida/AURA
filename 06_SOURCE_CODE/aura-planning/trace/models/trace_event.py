from dataclasses import dataclass,field
import time
@dataclass(frozen=True,slots=True)
class TraceEvent:
    name:str
    timestamp:float=field(default_factory=time.time)
    payload:dict=field(default_factory=dict)
    level:str="info"
