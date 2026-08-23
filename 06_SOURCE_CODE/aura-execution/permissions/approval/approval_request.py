from dataclasses import dataclass
@dataclass(frozen=True)
class Approval:
    action_id: str
    approved_by: str
    reason: str
