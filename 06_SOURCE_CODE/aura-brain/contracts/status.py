"""
AURA Contracts - Status
"""

from __future__ import annotations

from enum import Enum


class Status(Enum):
    """Execution status."""

    CREATED = "created"

    PENDING = "pending"

    RUNNING = "running"

    COMPLETED = "completed"

    FAILED = "failed"

    CANCELLED = "cancelled"

    RETRYING = "retrying"

    TIMEOUT = "timeout"