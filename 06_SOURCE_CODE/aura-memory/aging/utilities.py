"""AURA Memory Aging Utilities utilities."""

from __future__ import annotations
import json
import logging
import time
import uuid
from typing import Any, Dict

logger = logging.getLogger(__name__)


def serialize_UTILITIES(payload: Dict[str, Any]) -> str:
    """Serialize payload to JSON."""
    return json.dumps(payload, sort_keys=True, separators=(',', ':'))


def deserialize_UTILITIES(payload: str) -> Dict[str, Any]:
    """Deserialize payload from JSON."""
    return json.loads(payload)


def create_default_UTILITIES() -> Dict[str, Any]:
    """Create a default payload."""
    return {'id': str(uuid.uuid4()), 'name': 'default-UTILITIES', 'created_at': time.time()}

__all__ = ['serialize_UTILITIES', 'deserialize_UTILITIES', 'create_default_UTILITIES']
