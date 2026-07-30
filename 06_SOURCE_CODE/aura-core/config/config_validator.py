from __future__ import annotations

from typing import Dict, Any


class ConfigValidationError(Exception):
    pass


class ConfigValidator:
    def __init__(self, schema: Dict[str, Any] | None = None) -> None:
        self.schema = schema or {}

    def validate(self, config: Dict[str, Any]) -> None:
        # Implement schema-based validation when schema is provided.
        return
