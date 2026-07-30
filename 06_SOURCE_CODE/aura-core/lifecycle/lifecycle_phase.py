from __future__ import annotations

from dataclasses import dataclass
from typing import Callable


@dataclass
class LifecyclePhase:
    name: str
    action: Callable
