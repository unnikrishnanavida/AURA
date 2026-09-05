"""Result types and error taxonomy for aura-cli.

Commands return an :class:`ExitCode` (stable integer) and structured output.
Errors carry machine-readable codes so JSON output is always parseable.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


class ExitCode:
    """Stable CLI exit codes (documented, never changed)."""

    OK = 0
    FAILED = 1
    CONFIG_INVALID = 2
    NOT_FOUND = 3
    DENIED = 4
    NOT_SUPPORTED = 5
    INTERNAL_ERROR = 70


class CliError(Exception):
    """A recoverable CLI error with a stable code."""

    code = "cli.error"

    def __init__(self, message: str, *, code: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        if code:
            self.code = code


class ConfigInvalidError(CliError):
    code = "cli.config_invalid"


class NotFoundError(CliError):
    code = "cli.not_found"


class DeniedError(CliError):
    code = "cli.denied"


class NotSupportedError(CliError):
    code = "cli.not_supported"


@dataclass
class CommandResult:
    """Structured result of a CLI command."""

    exit_code: int = ExitCode.OK
    output: dict[str, Any] = field(default_factory=dict)
    human_lines: list[str] = field(default_factory=list)
    error: CliError | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "exit_code": self.exit_code,
            "ok": self.exit_code == ExitCode.OK,
            "data": self.output,
            "error": None if self.error is None else {"code": self.error.code, "message": self.error.message},
        }


__all__ = [
    "CliError",
    "CommandResult",
    "ConfigInvalidError",
    "DeniedError",
    "ExitCode",
    "NotFoundError",
    "NotSupportedError",
]