"""Dependency injection container used by the application.

This implementation is intentionally small, thread-safe, and
practical for bootstrapping components in the composition root.
It supports registering instances, factories and simple lifecycle
hooks (startup / shutdown).
"""

from __future__ import annotations

from typing import Any, Callable, Dict, Iterable, Tuple
import threading

Factory = Callable[["DependencyContainer"], Any]


class DependencyContainer:
    """A small dependency container.

    Usage patterns:
    - `register_instance(key, instance)` to register a ready object
    - `register_factory(key, factory, scope="singleton")` to register
      a factory that will be invoked with the container to create the
      instance. Supported scopes: `singleton`, `transient`.
    - `resolve(key)` to obtain the instance.
    """

    def __init__(self) -> None:
        self._singletons: Dict[Any, Any] = {}
        self._factories: Dict[Any, Tuple[Factory, str]] = {}
        self._startup_hooks: list[Callable[[], None]] = []
        self._shutdown_hooks: list[Callable[[], None]] = []
        self._lock = threading.RLock()

    def register_instance(self, key: Any, instance: Any) -> None:
        with self._lock:
            self._singletons[key] = instance

    def register_factory(self, key: Any, factory: Factory, *, scope: str = "singleton") -> None:
        if scope not in ("singleton", "transient"):
            raise ValueError("scope must be 'singleton' or 'transient'")
        with self._lock:
            self._factories[key] = (factory, scope)

    def resolve(self, key: Any) -> Any:
        """Resolve a dependency by key (type or string)."""
        with self._lock:
            if key in self._singletons:
                return self._singletons[key]

            if key in self._factories:
                factory, scope = self._factories[key]
                instance = factory(self)
                if scope == "singleton":
                    self._singletons[key] = instance
                return instance

            raise KeyError(f"No dependency registered for key: {key!r}")

    def register_startup(self, fn: Callable[[], None]) -> None:
        with self._lock:
            self._startup_hooks.append(fn)

    def register_shutdown(self, fn: Callable[[], None]) -> None:
        with self._lock:
            self._shutdown_hooks.append(fn)

    def run_startup(self) -> None:
        for fn in list(self._startup_hooks):
            try:
                fn()
            except Exception:
                # Keep startup robust; callers may log exceptions.
                pass

    def run_shutdown(self) -> None:
        for fn in list(self._shutdown_hooks):
            try:
                fn()
            except Exception:
                pass

    def list(self) -> Iterable[Any]:
        with self._lock:
            keys = set(self._singletons) | set(self._factories)
            return list(keys)

    def clear(self) -> None:
        with self._lock:
            self._singletons.clear()
            self._factories.clear()
            self._startup_hooks.clear()
            self._shutdown_hooks.clear()
