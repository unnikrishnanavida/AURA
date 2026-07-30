from __future__ import annotations

from typing import Callable, Any, Dict


class ScopedProvider:
    def __init__(self, factory: Callable[..., Any]) -> None:
        self._factory = factory
        self._instances: Dict[str, Any] = {}

    def get(self, scope_id: str) -> Any:
        if scope_id not in self._instances:
            self._instances[scope_id] = self._factory()
        return self._instances[scope_id]
