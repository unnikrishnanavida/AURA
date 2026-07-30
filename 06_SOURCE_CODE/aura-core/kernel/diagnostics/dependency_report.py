from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Dict


@dataclass
class DependencyReport:
    issues: List[Dict[str, str]] = field(default_factory=list)

    def add_issue(self, module: str, problem: str) -> None:
        self.issues.append({"module": module, "problem": problem})

    def has_issues(self) -> bool:
        return bool(self.issues)
