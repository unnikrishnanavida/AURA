"""AURA Memory Analytics Behavior Analytics utilities."""

from __future__ import annotations
import json
import logging
import time
import uuid
from typing import Any, Dict

logger = logging.getLogger(__name__)


def serialize_BEHAVIOR_ANALYTICS(payload: Dict[str, Any]) -> str:
    """Serialize payload to JSON."""
    return json.dumps(payload, sort_keys=True, separators=(',', ':'))


def deserialize_BEHAVIOR_ANALYTICS(payload: str) -> Dict[str, Any]:
    """Deserialize payload from JSON."""
    return json.loads(payload)


def create_default_BEHAVIOR_ANALYTICS() -> Dict[str, Any]:
    """Create a default payload."""
    return {'id': str(uuid.uuid4()), 'name': 'default-BEHAVIOR_ANALYTICS', 'created_at': time.time()}

__all__ = ['serialize_BEHAVIOR_ANALYTICS', 'deserialize_BEHAVIOR_ANALYTICS', 'create_default_BEHAVIOR_ANALYTICS']
