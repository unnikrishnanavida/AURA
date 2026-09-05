from dataclasses import dataclass
@dataclass(frozen=True,slots=True)
class MutationRecord:
    parent_id:str; child_id:str; changes:tuple
