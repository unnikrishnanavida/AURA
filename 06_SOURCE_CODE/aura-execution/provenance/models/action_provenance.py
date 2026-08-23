from dataclasses import dataclass
@dataclass(frozen=True)
class ActionProvenance:
    action_id:str
    source_plan:str|None=None
