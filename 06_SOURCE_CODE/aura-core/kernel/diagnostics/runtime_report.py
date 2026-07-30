from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Any


@dataclass
class RuntimeReport:
    metrics: Dict[str, Any] = field(default_factory=dict)

    def add_metric(self, name: str, value: Any) -> None:
        self.metrics[name] = value

    def as_dict(self) -> Dict[str, Any]:
        return dict(self.metrics)
