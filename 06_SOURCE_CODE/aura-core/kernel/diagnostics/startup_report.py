from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict, Any


@dataclass
class StartupReport:
    entries: List[Dict[str, Any]] = field(default_factory=list)

    def add(self, name: str, ok: bool, note: str | None = None) -> None:
        self.entries.append({"name": name, "ok": ok, "note": note})

    def summary(self) -> Dict[str, Any]:
        return {"total": len(self.entries), "entries": list(self.entries)}
