"""Tool output model."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass
class ToolOutput:
    """Result of invoking an external tool adapter."""

    success: bool
    value: Any = None
    error: str | None = None
    stdout: str = ""
    stderr: str = ""
    exit_code: int | None = None
    duration: float = 0.0


__all__ = ["ToolOutput"]