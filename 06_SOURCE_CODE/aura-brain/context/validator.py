"""Validation helpers for the context subsystem."""

from __future__ import annotations

from typing import Any


class ContextValidator:
    """Validate input objects and configuration."""

    def validate(self, value: Any) -> None:
        """Validate the supplied value."""
        if value is None:
            raise ValueError('Value cannot be None')
