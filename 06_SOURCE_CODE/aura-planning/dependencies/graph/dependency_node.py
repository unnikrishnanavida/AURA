from __future__ import annotations
from dataclasses import dataclass,field
@dataclass(slots=True)
class DependencyNode:
    node_id:str; payload:object=None; incoming:set[str]=field(default_factory=set); outgoing:set[str]=field(default_factory=set)
    def ready(self,completed:set[str])->bool: return self.incoming <= completed
