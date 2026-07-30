from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Any


@dataclass
class RuntimeContext:
    """Stores runtime-scoped objects such as request/session state."""

    data: Dict[str, Any] = field(default_factory=dict)

    def set(self, key: str, value: Any) -> None:
        self.data[key] = value

    def get(self, key: str, default=None):
        return self.data.get(key, default)
