"""Settings and preferences for aura-desktop backed by secure local storage."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from aura_desktop.security.storage import SecureLocalStorage


@dataclass
class SettingsStore:
    """Typed settings facade over a SecureLocalStorage backend."""

    storage: SecureLocalStorage
    _values: dict[str, Any] = field(default_factory=dict)

    def load(self, keys: list[str]) -> None:
        for key in keys:
            value = self.storage.get(key)
            if value is not None:
                self._values[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        return self._values.get(key, default)

    def set(self, key: str, value: Any) -> None:
        self._values[key] = value
        self.storage.set(key, value)


__all__ = ["SettingsStore"]