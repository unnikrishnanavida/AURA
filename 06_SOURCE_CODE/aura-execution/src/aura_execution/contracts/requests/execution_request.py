from dataclasses import dataclass, field
from typing import Any


@dataclass
class ExecutionRequest:
    action: Any
    inputs: dict[str, Any] = field(default_factory=dict)
    state: dict[str, Any] = field(default_factory=dict)
    approved: bool = False
    budget: dict[str, float] = field(default_factory=dict)
