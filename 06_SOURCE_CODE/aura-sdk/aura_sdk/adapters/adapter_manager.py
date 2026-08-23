"""AURA SDK Adapters adapter_manager.

Provides a simple registry-based manager used by many modules. The
`_impl` injector also attaches registry methods at import time; this
implementation ensures the class behaves sensibly when instantiated
directly (for tests and simple usage).
"""

class AdapterManager:
    """Manager for aura_sdk.adapters.adapter_manager.

    This class acts as a lightweight registry for adapter instances.
    It intentionally keeps behaviour minimal and predictable so that
    concrete adapter implementations can subclass or replace methods.
    """

    def __init__(self) -> None:
        self._registry = {}

    def register(self, name: str, adapter: object) -> None:
        if not name:
            raise ValueError("adapter name must be non-empty")
        self._registry[name] = adapter

    def unregister(self, name: str) -> object:
        try:
            return self._registry.pop(name)
        except KeyError:
            raise KeyError(f"adapter not found: {name}")

    def get(self, name: str, default: object = None) -> object:
        return self._registry.get(name, default)

    def list(self) -> list:
        return list(self._registry.keys())
