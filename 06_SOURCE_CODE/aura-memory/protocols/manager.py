"""AURA Memory protocols manager."""

from __future__ import annotations

import logging
import threading
from typing import Any, Callable, Dict, List, Optional, Protocol

logger = logging.getLogger(__name__)


class ProtocolHandler(Protocol):
    def execute(self, payload: Dict[str, Any]) -> Any:
        ...


class ProtocolManager:
    """Thread-safe protocol registration and execution manager."""

    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._handlers: Dict[str, ProtocolHandler] = {}

    def register(self, name: str, handler: ProtocolHandler) -> None:
        """Register a protocol handler by name."""
        if not name:
            raise ValueError("Protocol name must be non-empty")
        if not callable(getattr(handler, "execute", None)):
            raise ValueError("Protocol handler must implement execute(payload)")
        with self._lock:
            self._handlers[name] = handler
            logger.debug("Registered protocol %s", name)

    def resolve(self, name: str) -> Optional[ProtocolHandler]:
        """Return the registered handler for a protocol."""
        with self._lock:
            return self._handlers.get(name)

    def execute(self, name: str, payload: Dict[str, Any]) -> Any:
        """Execute the protocol handler for the given name."""
        handler = self.resolve(name)
        if handler is None:
            raise KeyError(f"Protocol '{name}' is not registered")
        return handler.execute(payload)

    def unregister(self, name: str) -> bool:
        """Unregister a protocol handler."""
        with self._lock:
            return self._handlers.pop(name, None) is not None

    def list_protocols(self) -> List[str]:
        """List all registered protocols."""
        with self._lock:
            return list(self._handlers.keys())


__all__ = ["ProtocolManager"]
