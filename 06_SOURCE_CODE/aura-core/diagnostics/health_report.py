from dataclasses import dataclass, field
from typing import Dict, Any


@dataclass
class HealthReport:
    status: str
    metrics: Dict[str, Any] = field(default_factory=dict)
