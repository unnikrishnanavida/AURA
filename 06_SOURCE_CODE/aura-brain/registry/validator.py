"""Validation utilities for registry entries and metadata."""

from __future__ import annotations

from .exceptions import RegistryValidationError
from .models import RegistryEntry


class RegistryValidator:
    """Validate registry entries before registration."""

    def validate(self, entry: RegistryEntry) -> None:
        """Validate a registry entry."""
        if not entry.name:
            raise RegistryValidationError("Registry entry name cannot be empty")
        if not entry.kind:
            raise RegistryValidationError("Registry entry kind cannot be empty")
        if not isinstance(entry.data, dict):
            raise RegistryValidationError("Registry entry data must be a dictionary")

    def validate_many(self, entries: list[RegistryEntry]) -> None:
        """Validate a collection of entries."""
        for entry in entries:
            self.validate(entry)
