from dataclasses import dataclass
@dataclass(frozen=True)
class ProvenanceNode:
    id:str
    kind:str
