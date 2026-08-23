from dataclasses import dataclass
@dataclass
class CancelRequest:
    execution_id: str
    reason: str = "cancelled by caller"
