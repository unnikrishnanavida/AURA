"""AURA SDK Diagnostics diagnostics_manager.
"""

"""AURA SDK Diagnostics diagnostics_manager.

Tracks simple diagnostic messages and severity levels. Designed for
lightweight integration with monitoring components.
"""

from typing import List, Tuple


class DiagnosticsManager:
    """Manager for aura_sdk.diagnostics.diagnostics_manager."""

    def __init__(self) -> None:
        self._messages: List[Tuple[str, str]] = []  # (severity, message)

    def add(self, severity: str, message: str) -> None:
        if severity not in ("info", "warning", "error"):
            raise ValueError("severity must be 'info', 'warning' or 'error'")
        self._messages.append((severity, message))

    def clear(self) -> None:
        self._messages.clear()

    def list(self) -> List[Tuple[str, str]]:
        return list(self._messages)

    def has_errors(self) -> bool:
        return any(s == "error" for s, _ in self._messages)
