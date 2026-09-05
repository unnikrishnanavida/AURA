"""Serialization helpers.

`to_jsonable` converts dataclasses, enums, datetimes, exceptions and
Result/Status values into JSON-serializable primitives. `json_dumps`
serializes with an optional schema-version envelope.
"""

from __future__ import annotations

import dataclasses
import json
from datetime import date, datetime
from enum import Enum
from typing import Any

from aura.foundation.errors import AuraError

_SCHEMA_VERSION = 1


def to_jsonable(value: Any) -> Any:
    """Recursively convert a value into JSON-serializable primitives."""
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, AuraError):
        return {"code": value.code, "message": value.message}
    if dataclasses.is_dataclass(value):
        return {
            f.name: to_jsonable(getattr(value, f.name))
            for f in dataclasses.fields(value)
            if f.init
        }
    if isinstance(value, dict):
        return {str(k): to_jsonable(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [to_jsonable(v) for v in value]
    if hasattr(value, "to_dict") and callable(value.to_dict):
        return to_jsonable(value.to_dict())
    return str(value)


def json_dumps(value: Any, *, schema_version: int = _SCHEMA_VERSION) -> str:
    """Serialize `value` to JSON with a schema-version envelope."""
    payload: Any = to_jsonable(value)
    return json.dumps({"schema_version": schema_version, "payload": payload}, sort_keys=True)


__all__ = ["json_dumps", "to_jsonable"]