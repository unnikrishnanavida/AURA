from dataclasses import dataclass, field
from typing import Any
@dataclass
class ActionResult:
    success: bool
    value: Any = None
    error: str | None = None
    duration: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)
