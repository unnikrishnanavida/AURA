"""
Runtime Metrics
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class RuntimeMetrics:
    """Runtime statistics."""

    submitted_tasks: int = 0

    completed_tasks: int = 0

    failed_tasks: int = 0

    active_workers: int = 0

    queued_tasks: int = 0

    uptime_seconds: float = 0.0