"""Minimal dependency-injection container.

Engine services depend on abstractions; the container binds them at wiring
time. Resolution is explicit and cycle detecting. This is the single DI
mechanism in AURA.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

from aura.foundation.errors import LifecycleError, NotFoundError

Factory = Callable[["Container"], Any]


class Container:
    """Binds interfaces to implementations or factories.

    - ``singleton(factory)`` -> one instance shared forever
    - ``transient(factory)`` -> a fresh instance per resolve
    - ``bind(value)``        -> an already-constructed instance
    """

    def __init__(self, parent: Container | None = None) -> None:
        self._factories: dict[type, tuple[str, Factory]] = {}
        self._values: dict[type, Any] = {}
        self._singletons: dict[type, Any] = {}
        self._resolving: set[type] = set()
        self._parent = parent

    def singleton(self, interface: type, factory: Factory) -> Container:
        self._factories[interface] = ("singleton", factory)
        return self

    def transient(self, interface: type, factory: Factory) -> Container:
        self._factories[interface] = ("transient", factory)
        return self

    def bind(self, interface: type, instance: Any) -> Container:
        self._values[interface] = instance
        return self

    def resolve(self, interface: type) -> Any:
        if interface in self._values:
            return self._values[interface]
        if interface in self._factories:
            kind, factory = self._factories[interface]
            if kind == "singleton":
                if interface in self._singletons:
                    return self._singletons[interface]
                if interface in self._resolving:
                    raise LifecycleError(f"circular dependency while resolving {interface.__name__}")
                self._resolving.add(interface)
                instance = factory(self)
                self._resolving.discard(interface)
                self._singletons[interface] = instance
                return instance
            return factory(self)
        if self._parent is not None:
            return self._parent.resolve(interface)
        raise NotFoundError(f"no binding registered for {interface.__name__}")

    def registered(self, interface: type) -> bool:
        return interface in self._values or interface in self._factories


__all__ = ["Container"]