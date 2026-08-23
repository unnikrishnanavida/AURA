from dataclasses import dataclass
@dataclass(frozen=True,slots=True)
class TraceNode:
    node_id:str
    kind:str
    payload:object=None
