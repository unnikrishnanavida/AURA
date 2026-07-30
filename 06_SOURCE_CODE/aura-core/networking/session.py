from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Any


@dataclass
class Session:
    id: str
    data: Dict[str, Any] = field(default_factory=dict)
