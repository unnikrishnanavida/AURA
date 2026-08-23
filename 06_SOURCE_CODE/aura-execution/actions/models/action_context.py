from dataclasses import dataclass, field
from typing import Any
@dataclass
class ActionContext:
    execution_id: str
    state: dict[str, Any] = field(default_factory=dict)
    inputs: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
