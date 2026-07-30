from __future__ import annotations

from typing import Dict, Any, Callable

from .exceptions import DIError


class Injector:
    def __init__(self) -> None:
        self._registry: Dict[str, Callable[..., Any]] = {}
        self._singletons: Dict[str, Any] = {}

    def register(self, name: str, factory: Callable[..., Any], singleton: bool = True) -> None:
        self._registry[name] = (factory, singleton)

    def get(self, name: str) -> Any:
        entry = self._registry.get(name)
        if not entry:
            raise DIError(f"No registration for {name}")
        factory, singleton = entry
        if singleton:
            if name not in self._singletons:
                self._singletons[name] = factory()
            return self._singletons[name]
        return factory()
