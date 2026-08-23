"""Very small dependency injection container."""

from typing import Any, Callable, Dict

_registry: Dict[str, Callable[[], Any]] = {}


def register(name: str, factory: Callable[[], Any]) -> None:
    _registry[name] = factory


def resolve(name: str) -> Any:
    factory = _registry.get(name)
    if factory is None:
        raise KeyError(f"Dependency '{name}' not registered")
    return factory()


__all__ = ["register", "resolve"]
