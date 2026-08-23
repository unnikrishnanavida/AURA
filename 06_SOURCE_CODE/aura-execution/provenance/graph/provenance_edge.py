from dataclasses import dataclass
@dataclass(frozen=True)
class ProvenanceEdge:
    source:str
    target:str
    relation:str
