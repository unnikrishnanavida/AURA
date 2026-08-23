"""Core infrastructure primitives for AURA Memory."""

from .constants import APP_NAME, APP_VERSION, DEFAULT_LOG_LEVEL
from .exceptions import AuraError, NotFoundError, ValidationError
from .models import BaseModel
from .schemas import dump_schema, validate_schema
from .types import JSON, JSONLike, Key, Value

__all__ = [
    "APP_NAME",
    "APP_VERSION",
    "DEFAULT_LOG_LEVEL",
    "AuraError",
    "NotFoundError",
    "ValidationError",
    "BaseModel",
    "dump_schema",
    "validate_schema",
    "JSON",
    "JSONLike",
    "Key",
    "Value",
]
