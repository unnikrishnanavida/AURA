AURA Memory utilities utilities for logging_utils.

from __future__ import annotations
import json
import logging
import time
import uuid
from typing import Any, Dict

logger = logging.getLogger(__name__)


def serialize_LOGGING_UTILS(payload: Dict[str, Any]) -> str:
    '''Serialize payload to a compact JSON string.'''
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def deserialize_LOGGING_UTILS(payload: str) -> Dict[str, Any]:
    '''Deserialize payload from JSON.'''
    return json.loads(payload)


def create_default_LOGGING_UTILS() -> Dict[str, Any]:
    '''Create a default payload object.'''
    return {"id": str(uuid.uuid4()), "name": "default-LOGGING_UTILS", "created_at": time.time()}


def normalize_LOGGING_UTILS(payload: Dict[str, Any]) -> Dict[str, Any]:
    '''Normalize a payload into a consistent shape.'''
    payload = payload.copy()
    payload.setdefault("id", str(uuid.uuid4()))
    payload.setdefault("name", "default-LOGGING_UTILS")
    payload.setdefault("created_at", time.time())
    return payload


__all__ = [
    "serialize_LOGGING_UTILS",
    "deserialize_LOGGING_UTILS",
    "create_default_LOGGING_UTILS",
    "normalize_LOGGING_UTILS",
]
