from dataclasses import dataclass
@dataclass
class ResumeRequest:
    execution_id: str
    checkpoint_id: str
