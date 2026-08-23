"""AURA SDK Discovery validator."""

from __future__ import annotations
from typing import Any


class Validator:
    """Core validator for aura_sdk.discovery."""

    def validate(self, data: Any) -> bool:
        """Return true when data is not None."""
        if data is None:
            raise ValueError("data cannot be None")
        return True
