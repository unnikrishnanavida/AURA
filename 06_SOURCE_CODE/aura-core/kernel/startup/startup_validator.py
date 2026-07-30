from __future__ import annotations

from typing import Iterable


class StartupValidationError(Exception):
    pass


class StartupValidator:
    def __init__(self, checks: Iterable[callable] | None = None) -> None:
        self.checks = list(checks or [])

    def add_check(self, check: callable) -> None:
        self.checks.append(check)

    def validate(self) -> None:
        for check in self.checks:
            check()
