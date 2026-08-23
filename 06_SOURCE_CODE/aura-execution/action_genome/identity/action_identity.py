from dataclasses import dataclass
@dataclass(frozen=True)
class ActionIdentity:
    action_id:str
    fingerprint:str
