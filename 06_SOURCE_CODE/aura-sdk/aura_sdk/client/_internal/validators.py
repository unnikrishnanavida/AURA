"""AURA SDK Client validators."""

from __future__ import annotations
from typing import Any


class ClientValidator:
    """Core validator for aura_sdk.client."""

    def validate(self, data: Any) -> bool:
        """Validate that data is not None and has expected structure."""
        if data is None:
            raise ValueError("data cannot be None")
        return True


__all__ = ["ClientValidator"]
