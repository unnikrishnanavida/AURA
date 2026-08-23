from dataclasses import dataclass
from uuid import uuid4
@dataclass(frozen=True)
class AttemptId:
    value: str
    @classmethod
    def new(cls): return cls(str(uuid4()))
