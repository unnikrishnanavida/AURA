from dataclasses import dataclass
@dataclass(frozen=True)
class ActionLineage:
    action_id:str
    parent:str|None=None
