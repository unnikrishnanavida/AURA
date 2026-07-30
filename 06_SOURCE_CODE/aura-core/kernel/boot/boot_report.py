from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict, Any


@dataclass
class BootReport:
    """Collects information emitted during boot for diagnostics."""

    entries: List[Dict[str, Any]] = field(default_factory=list)

    def add(self, name: str, status: str, details: dict | None = None) -> None:
        self.entries.append({"name": name, "status": status, "details": details or {}})

    def as_dict(self) -> dict:
        return {"entries": list(self.entries)}
