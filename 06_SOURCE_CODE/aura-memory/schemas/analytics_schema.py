AURA Memory schemas utilities for analytics_schema.

from __future__ import annotations
import json
import logging
import time
import uuid
from typing import Any, Dict

logger = logging.getLogger(__name__)


def serialize_ANALYTICS_SCHEMA(payload: Dict[str, Any]) -> str:
    '''Serialize payload to a compact JSON string.'''
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def deserialize_ANALYTICS_SCHEMA(payload: str) -> Dict[str, Any]:
    '''Deserialize payload from JSON.'''
    return json.loads(payload)


def create_default_ANALYTICS_SCHEMA() -> Dict[str, Any]:
    '''Create a default payload object.'''
    return {"id": str(uuid.uuid4()), "name": "default-ANALYTICS_SCHEMA", "created_at": time.time()}


def normalize_ANALYTICS_SCHEMA(payload: Dict[str, Any]) -> Dict[str, Any]:
    '''Normalize a payload into a consistent shape.'''
    payload = payload.copy()
    payload.setdefault("id", str(uuid.uuid4()))
    payload.setdefault("name", "default-ANALYTICS_SCHEMA")
    payload.setdefault("created_at", time.time())
    return payload


__all__ = [
    "serialize_ANALYTICS_SCHEMA",
    "deserialize_ANALYTICS_SCHEMA",
    "create_default_ANALYTICS_SCHEMA",
    "normalize_ANALYTICS_SCHEMA",
]
