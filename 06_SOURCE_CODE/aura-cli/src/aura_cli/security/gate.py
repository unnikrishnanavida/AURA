"""Security boundaries for aura-cli.

Dangerous operations require confirmation. In non-interactive mode there is no
confirmation path, so dangerous operations fail closed unless an explicit
``--yes`` flag is present.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from aura_cli.core.result import DeniedError


@dataclass(frozen=True)
class CommandPolicy:
    """Declares which commands are dangerous (require confirmation)."""

    dangerous: tuple[str, ...] = (
        "security_audit",
        "learning_apply",
        "memory_write",
        "plugin_install",
        "system_shutdown",
    )

    def requires_confirmation(self, command: str) -> bool:
        return command in self.dangerous


@dataclass
class ConfirmationGate:
    """Enforces confirmation for dangerous operations."""

    policy: CommandPolicy = field(default_factory=CommandPolicy)
    non_interactive: bool = False
    confirmed: set[str] = field(default_factory=set)

    def confirm(self, command: str) -> None:
        """Fail closed unless the operator explicitly confirmed the operation."""
        if not self.policy.requires_confirmation(command):
            return
        if self.non_interactive and command not in self.confirmed:
            raise DeniedError(
                f"operation {command!r} is dangerous and requires explicit confirmation; "
                "non-interactive mode fails closed (use --yes to confirm)"
            )


__all__ = ["CommandPolicy", "ConfirmationGate"]