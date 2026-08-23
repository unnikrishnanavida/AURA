"""AURA SDK Capability capability_manager.
"""

"""AURA SDK Capability capability_manager.

Capability manager tracks feature flags or capabilities available
within a runtime. The API is intentionally small and thread-safe for
basic uses.
"""

from threading import Lock


class CapabilityManager:
    """Manager for aura_sdk.capability.capability_manager."""

    def __init__(self) -> None:
        self._capabilities = set()
        self._lock = Lock()

    def enable(self, name: str) -> None:
        if not name:
            raise ValueError("capability name must be non-empty")
        with self._lock:
            self._capabilities.add(name)

    def disable(self, name: str) -> None:
        with self._lock:
            self._capabilities.discard(name)

    def is_enabled(self, name: str) -> bool:
        return name in self._capabilities

    def list(self) -> list:
        return sorted(self._capabilities)
