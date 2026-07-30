from __future__ import annotations

from typing import Callable, Dict


class HealthChecker:
    """Run registered health checks and return statuses."""

    def __init__(self) -> None:
        self._checks: Dict[str, Callable[[], bool]] = {}

    def register(self, name: str, check: Callable[[], bool]) -> None:
        self._checks[name] = check

    def run(self) -> Dict[str, bool]:
        return {n: bool(c()) for n, c in self._checks.items()}
