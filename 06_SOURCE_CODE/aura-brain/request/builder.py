"""Factory helpers for the request subsystem."""

from __future__ import annotations

from typing import Any


class Builder:
    """Create components for request."""

    def create(self, *args: Any, **kwargs: Any) -> Any:
        """Create a component instance."""
        return {'args': args, 'kwargs': kwargs}
