"""Synchronisation helpers for keeping registries consistent."""

from __future__ import annotations

from typing import Iterable

from .models import RegistryEntry


class RegistrySynchronizer:
    """Apply a set of registry entries to a target registry implementation."""

    def sync(self, target: object, entries: Iterable[RegistryEntry]) -> list[RegistryEntry]:
        """Register each entry in the target registry when it exposes a register method."""
        registered: list[RegistryEntry] = []
        for entry in entries:
            register_method = getattr(target, "register", None)
            if callable(register_method):
                register_method(entry.name, entry.data.get("model_type") or entry.data.get("plugin_type") or entry.kind)
                registered.append(entry)
        return registered
