from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable


@dataclass
class ServiceDescriptor:
    """Describes a service providing factory and lifecycle hooks."""

    name: str
    factory: Callable[..., Any]
    singleton: bool = True
