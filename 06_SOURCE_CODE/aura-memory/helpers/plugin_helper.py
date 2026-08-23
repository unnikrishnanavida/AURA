AURA Memory helpers utilities for plugin_helper.

from __future__ import annotations
import json
import logging
import time
import uuid
from typing import Any, Dict

logger = logging.getLogger(__name__)


def serialize_PLUGIN_HELPER(payload: Dict[str, Any]) -> str:
    '''Serialize payload to a compact JSON string.'''
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def deserialize_PLUGIN_HELPER(payload: str) -> Dict[str, Any]:
    '''Deserialize payload from JSON.'''
    return json.loads(payload)


def create_default_PLUGIN_HELPER() -> Dict[str, Any]:
    '''Create a default payload object.'''
    return {"id": str(uuid.uuid4()), "name": "default-PLUGIN_HELPER", "created_at": time.time()}


def normalize_PLUGIN_HELPER(payload: Dict[str, Any]) -> Dict[str, Any]:
    '''Normalize a payload into a consistent shape.'''
    payload = payload.copy()
    payload.setdefault("id", str(uuid.uuid4()))
    payload.setdefault("name", "default-PLUGIN_HELPER")
    payload.setdefault("created_at", time.time())
    return payload


__all__ = [
    "serialize_PLUGIN_HELPER",
    "deserialize_PLUGIN_HELPER",
    "create_default_PLUGIN_HELPER",
    "normalize_PLUGIN_HELPER",
]
