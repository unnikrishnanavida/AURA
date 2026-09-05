from dataclasses import dataclass
@dataclass(frozen=True,slots=True)
class TraceRecord:
    trace_id:str
    events:tuple
    metadata:dict
