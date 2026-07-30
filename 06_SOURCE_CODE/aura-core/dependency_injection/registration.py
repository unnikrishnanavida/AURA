from __future__ import annotations

from typing import Callable, Any


class Registration:
    def __init__(self, name: str, factory: Callable[..., Any], scope: str = "singleton") -> None:
        self.name = name
        self.factory = factory
        self.scope = scope
