from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


@dataclass
class StartupTask:
    """Represents a single startup task callable."""

    name: str
    action: Callable

    def run(self, kernel) -> None:
        return self.action(kernel)
