"""AURA Memory dependency_injection manager."""

from __future__ import annotations

import logging
import threading
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)

DependencyFactory = Callable[[], Any]


class DependencyInjectionManager:
    """Thread-safe dependency injection container."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._providers: Dict[str, DependencyFactory] = {}
        self._singletons: Dict[str, Any] = {}

    def register(self, key: str, factory: DependencyFactory, singleton: bool = False) -> None:
        """Register a provider factory under a key."""
        if not key:
            raise ValueError("Dependency key must be non-empty")
        if not callable(factory):
            raise ValueError("Dependency factory must be callable")
        with self._lock:
            self._providers[key] = factory
            if singleton:
                self._singletons.pop(key, None)
            logger.debug("Registered dependency %s singleton=%s", key, singleton)

    def resolve(self, key: str, default: Optional[Any] = None) -> Any:
        """Resolve a registered provider by key."""
        with self._lock:
            provider = self._providers.get(key)
            if provider is None:
                if default is not None:
                    return default
                raise KeyError(f"Dependency '{key}' is not registered")
            return provider()

    def resolve_singleton(self, key: str) -> Any:
        """Resolve a registered provider as a singleton instance."""
        with self._lock:
            provider = self._providers.get(key)
            if provider is None:
                raise KeyError(f"Dependency '{key}' is not registered")
            if key not in self._singletons:
                self._singletons[key] = provider()
            return self._singletons[key]

    def unregister(self, key: str) -> bool:
        """Unregister a dependency."""
        with self._lock:
            removed = self._providers.pop(key, None) is not None
            self._singletons.pop(key, None)
            logger.debug("Unregistered dependency %s", key)
            return removed

    def clear(self) -> None:
        """Clear all registered dependencies."""
        with self._lock:
            self._providers.clear()
            self._singletons.clear()
            logger.debug("Cleared all dependencies")

    def list_dependencies(self) -> Dict[str, bool]:
        """List registered dependency keys and whether a singleton exists."""
        with self._lock:
            return {key: key in self._singletons for key in self._providers}


__all__ = ["DependencyInjectionManager"]
