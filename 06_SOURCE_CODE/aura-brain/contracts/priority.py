"""
AURA Contracts - Priority
"""

from __future__ import annotations

from enum import IntEnum


class Priority(IntEnum):
    """Priority levels."""

    LOW = 1

    NORMAL = 5

    HIGH = 8

    CRITICAL = 10