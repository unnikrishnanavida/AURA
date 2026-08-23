AURA Memory providers utilities for analytics_provider.

from __future__ import annotations
import json
import logging
import time
import uuid
from typing import Any, Dict

logger = logging.getLogger(__name__)


def serialize_ANALYTICS_PROVIDER(payload: Dict[str, Any]) -> str:
    '''Serialize payload to a compact JSON string.'''
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def deserialize_ANALYTICS_PROVIDER(payload: str) -> Dict[str, Any]:
    '''Deserialize payload from JSON.'''
    return json.loads(payload)


def create_default_ANALYTICS_PROVIDER() -> Dict[str, Any]:
    '''Create a default payload object.'''
    return {"id": str(uuid.uuid4()), "name": "default-ANALYTICS_PROVIDER", "created_at": time.time()}


def normalize_ANALYTICS_PROVIDER(payload: Dict[str, Any]) -> Dict[str, Any]:
    '''Normalize a payload into a consistent shape.'''
    payload = payload.copy()
    payload.setdefault("id", str(uuid.uuid4()))
    payload.setdefault("name", "default-ANALYTICS_PROVIDER")
    payload.setdefault("created_at", time.time())
    return payload


__all__ = [
    "serialize_ANALYTICS_PROVIDER",
    "deserialize_ANALYTICS_PROVIDER",
    "create_default_ANALYTICS_PROVIDER",
    "normalize_ANALYTICS_PROVIDER",
]
