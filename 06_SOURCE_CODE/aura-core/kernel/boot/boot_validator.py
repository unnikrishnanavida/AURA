from __future__ import annotations

from typing import List


class BootValidationError(Exception):
    pass


class BootValidator:
    """Validate that required boot conditions are met before startup."""

    def __init__(self, checks: List[callable] | None = None) -> None:
        self.checks = list(checks or [])

    def add_check(self, check: callable) -> None:
        self.checks.append(check)

    def validate(self) -> None:
        errors = []
        for check in self.checks:
            try:
                check()
            except Exception as exc:  # pragma: no cover - surface errors
                errors.append(str(exc))
        if errors:
            raise BootValidationError("; ".join(errors))
