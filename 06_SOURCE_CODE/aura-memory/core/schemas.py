"""Core JSON schema helpers."""

from __future__ import annotations

import json
from typing import Any, Dict, Optional


def validate_schema(instance: Dict[str, Any], schema: Dict[str, Any]) -> Optional[str]:
    """Lightweight schema validator. Returns error message or None on success.

    Note: For production use, replace with `jsonschema` or `pydantic` validation.
    """
    # very small-checks: required keys presence
    required = schema.get("required") or []
    for key in required:
        if key not in instance:
            return f"Missing required key: {key}"
    return None


def dump_schema(schema: Dict[str, Any]) -> str:
    return json.dumps(schema, sort_keys=True, indent=2)


__all__ = ["validate_schema", "dump_schema"]
