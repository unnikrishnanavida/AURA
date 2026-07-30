from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass
class KernelContext:
    """Thin typed bag for sharing objects between kernel subsystems."""

    values: Dict[str, Any] = field(default_factory=dict)

    def register(self, name: str, value: Any) -> None:
        self.values[name] = value

    def resolve(self, name: str) -> Optional[Any]:
        return self.values.get(name)

    def as_dict(self) -> Dict[str, Any]:
        return dict(self.values)
