AURA Memory decision utilities for utility_functions.

from __future__ import annotations
import json
import logging
import time
import uuid
from typing import Any, Dict

logger = logging.getLogger(__name__)


def serialize_UTILITY_FUNCTIONS(payload: Dict[str, Any]) -> str:
    '''Serialize payload to a compact JSON string.'''
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def deserialize_UTILITY_FUNCTIONS(payload: str) -> Dict[str, Any]:
    '''Deserialize payload from JSON.'''
    return json.loads(payload)


def create_default_UTILITY_FUNCTIONS() -> Dict[str, Any]:
    '''Create a default payload object.'''
    return {"id": str(uuid.uuid4()), "name": "default-UTILITY_FUNCTIONS", "created_at": time.time()}


def normalize_UTILITY_FUNCTIONS(payload: Dict[str, Any]) -> Dict[str, Any]:
    '''Normalize a payload into a consistent shape.'''
    payload = payload.copy()
    payload.setdefault("id", str(uuid.uuid4()))
    payload.setdefault("name", "default-UTILITY_FUNCTIONS")
    payload.setdefault("created_at", time.time())
    return payload


__all__ = [
    "serialize_UTILITY_FUNCTIONS",
    "deserialize_UTILITY_FUNCTIONS",
    "create_default_UTILITY_FUNCTIONS",
    "normalize_UTILITY_FUNCTIONS",
]
