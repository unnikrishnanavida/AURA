from __future__ import annotations

from dataclasses import dataclass, field
from typing import List


@dataclass
class ValidationResult:
    valid: bool = True
    errors: List[str] = field(default_factory=list)
