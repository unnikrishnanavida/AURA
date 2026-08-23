"""AURA Memory Analytics Memory Analytics utilities."""

from __future__ import annotations
import json
import logging
import time
import uuid
from typing import Any, Dict

logger = logging.getLogger(__name__)


def serialize_MEMORY_ANALYTICS(payload: Dict[str, Any]) -> str:
    """Serialize payload to JSON."""
    return json.dumps(payload, sort_keys=True, separators=(',', ':'))


def deserialize_MEMORY_ANALYTICS(payload: str) -> Dict[str, Any]:
    """Deserialize payload from JSON."""
    return json.loads(payload)


def create_default_MEMORY_ANALYTICS() -> Dict[str, Any]:
    """Create a default payload."""
    return {'id': str(uuid.uuid4()), 'name': 'default-MEMORY_ANALYTICS', 'created_at': time.time()}

__all__ = ['serialize_MEMORY_ANALYTICS', 'deserialize_MEMORY_ANALYTICS', 'create_default_MEMORY_ANALYTICS']
