from __future__ import annotations

from typing import Any, Dict


class ConfigParser:
    """Normalize and validate raw config mappings into canonical form."""

    def parse(self, raw: Dict[str, Any]) -> Dict[str, Any]:
        # For now, return raw; hook point for environment variable expansion,
        # type coercion, and schema validation.
        return dict(raw)
