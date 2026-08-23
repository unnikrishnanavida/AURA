from dataclasses import dataclass
@dataclass(frozen=True,slots=True)
class TraceEdge:
    source:str
    target:str
    relation:str
