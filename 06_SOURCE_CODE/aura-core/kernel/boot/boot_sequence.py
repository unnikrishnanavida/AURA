from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Callable


@dataclass
class BootSequence:
    """Describes an ordered list of boot steps."""

    steps: List[Callable] = field(default_factory=list)

    def add(self, step: Callable) -> None:
        self.steps.append(step)

    def extend(self, steps: List[Callable]) -> None:
        self.steps.extend(steps)

    def __iter__(self):
        return iter(self.steps)
