AURA Memory knowledge_universe utilities for universe_metrics.

from __future__ import annotations
import json
import logging
import time
import uuid
from typing import Any, Dict

logger = logging.getLogger(__name__)


def serialize_UNIVERSE_METRICS(payload: Dict[str, Any]) -> str:
    '''Serialize payload to a compact JSON string.'''
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def deserialize_UNIVERSE_METRICS(payload: str) -> Dict[str, Any]:
    '''Deserialize payload from JSON.'''
    return json.loads(payload)


def create_default_UNIVERSE_METRICS() -> Dict[str, Any]:
    '''Create a default payload object.'''
    return {"id": str(uuid.uuid4()), "name": "default-UNIVERSE_METRICS", "created_at": time.time()}


def normalize_UNIVERSE_METRICS(payload: Dict[str, Any]) -> Dict[str, Any]:
    '''Normalize a payload into a consistent shape.'''
    payload = payload.copy()
    payload.setdefault("id", str(uuid.uuid4()))
    payload.setdefault("name", "default-UNIVERSE_METRICS")
    payload.setdefault("created_at", time.time())
    return payload


__all__ = [
    "serialize_UNIVERSE_METRICS",
    "deserialize_UNIVERSE_METRICS",
    "create_default_UNIVERSE_METRICS",
    "normalize_UNIVERSE_METRICS",
]
