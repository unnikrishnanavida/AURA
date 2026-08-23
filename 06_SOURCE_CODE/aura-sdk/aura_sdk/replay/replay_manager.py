"""AURA SDK Replay replay_manager.
"""

class ReplayManager:
    """Manager for aura_sdk.replay.replay_manager."""

    def __init__(self):

            def __init__(self) -> None:
                self._registry = {}

            def register(self, name: str, obj: object) -> None:
                if not name:
                    raise ValueError("name must be non-empty")
                self._registry[name] = obj

            def unregister(self, name: str) -> object:
                try:
                    return self._registry.pop(name)
                except KeyError:
                    raise KeyError(f"not registered: {name}")

            def get(self, name: str, default: object = None) -> object:
                return self._registry.get(name, default)

            def list(self) -> list:
                return list(self._registry.keys())

