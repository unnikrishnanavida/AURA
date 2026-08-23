"""AURA Memory Agi Agi Metrics utilities."""

from __future__ import annotations
import json
import logging
import time
import uuid
from typing import Any, Dict

logger = logging.getLogger(__name__)


def serialize_AGI_METRICS(payload: Dict[str, Any]) -> str:
    """Serialize payload to JSON."""
    return json.dumps(payload, sort_keys=True, separators=(',', ':'))


def deserialize_AGI_METRICS(payload: str) -> Dict[str, Any]:
    """Deserialize payload from JSON."""
    return json.loads(payload)


def create_default_AGI_METRICS() -> Dict[str, Any]:
    """Create a default payload."""
    return {'id': str(uuid.uuid4()), 'name': 'default-AGI_METRICS', 'created_at': time.time()}

__all__ = ['serialize_AGI_METRICS', 'deserialize_AGI_METRICS', 'create_default_AGI_METRICS']
