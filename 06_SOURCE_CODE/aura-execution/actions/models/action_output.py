from dataclasses import dataclass, field
from typing import Any
@dataclass
class ActionOutput:
    success: bool
    value: Any = None
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
