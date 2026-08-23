from dataclasses import dataclass
@dataclass
class ApprovalRequest:
    execution_id: str
    action_id: str
    reason: str
