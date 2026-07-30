from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Any


@dataclass
class ProviderDescriptor:
    name: str
    provider: Callable[..., Any]
    scope: str = "singleton"
