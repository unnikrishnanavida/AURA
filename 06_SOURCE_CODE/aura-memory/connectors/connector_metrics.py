AURA Memory connectors utilities for connector_metrics.

from __future__ import annotations
import json
import logging
import time
import uuid
from typing import Any, Dict

logger = logging.getLogger(__name__)


def serialize_CONNECTOR_METRICS(payload: Dict[str, Any]) -> str:
    '''Serialize payload to a compact JSON string.'''
    return json.dumps(payload, sort_keys=True, separators=(",", ":"))


def deserialize_CONNECTOR_METRICS(payload: str) -> Dict[str, Any]:
    '''Deserialize payload from JSON.'''
    return json.loads(payload)


def create_default_CONNECTOR_METRICS() -> Dict[str, Any]:
    '''Create a default payload object.'''
    return {"id": str(uuid.uuid4()), "name": "default-CONNECTOR_METRICS", "created_at": time.time()}


def normalize_CONNECTOR_METRICS(payload: Dict[str, Any]) -> Dict[str, Any]:
    '''Normalize a payload into a consistent shape.'''
    payload = payload.copy()
    payload.setdefault("id", str(uuid.uuid4()))
    payload.setdefault("name", "default-CONNECTOR_METRICS")
    payload.setdefault("created_at", time.time())
    return payload


__all__ = [
    "serialize_CONNECTOR_METRICS",
    "deserialize_CONNECTOR_METRICS",
    "create_default_CONNECTOR_METRICS",
    "normalize_CONNECTOR_METRICS",
]
