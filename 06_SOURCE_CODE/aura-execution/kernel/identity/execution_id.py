from dataclasses import dataclass
from uuid import uuid4

@dataclass(frozen=True)
class ExecutionId:
    value: str
    @classmethod
    def new(cls): return cls(str(uuid4()))
    def __str__(self): return self.value
