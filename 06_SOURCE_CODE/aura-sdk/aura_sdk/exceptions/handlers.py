"""AURA SDK Exceptions handlers."""


class HandlerException(Exception):
    """Base exception raised by exception handlers."""


class ExceptionHandler:
    """Core handlers for aura_sdk.exceptions."""

    def handle(self, event: object) -> dict[str, object]:
        """Handle an error event and return a safe fallback object."""
        if event is None:
            raise HandlerException("event cannot be None")
        return {"status": "handled", "event": event}
