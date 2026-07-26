"""Validation helpers for the pipeline subsystem."""

from __future__ import annotations

from typing import Any


class PipelineValidator:
    """Validate input objects and configuration."""

    def validate(self, value: Any) -> None:
        """Validate the supplied value."""
        if value is None:
            raise ValueError('Value cannot be None')
