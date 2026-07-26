"""
AURA Contracts - Envelope
"""

from __future__ import annotations

from dataclasses import dataclass

from .message import Message


@dataclass(slots=True)
class Envelope:
    """Wraps a transport message."""

    message: Message

    correlation_id: str

    trace_id: str