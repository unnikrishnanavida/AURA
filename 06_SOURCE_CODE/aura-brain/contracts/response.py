"""
AURA Contracts - Response
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(slots=True)
class Response:
    """Represents a response."""

    success: bool

    data: Any = None

    message: str = ""