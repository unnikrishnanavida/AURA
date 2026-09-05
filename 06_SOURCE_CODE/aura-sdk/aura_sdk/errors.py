"""AURA SDK error hierarchy.

Every SDK failure is a typed exception with a stable machine-readable code, so
callers can branch on failure class instead of parsing messages. Server-side
``AuraError`` codes are surfaced unchanged where available.
"""

from __future__ import annotations


class SdkError(Exception):
    """Base class for all aura-sdk errors."""

    code = "sdk.error"

    def __init__(self, message: str, *, request_id: str | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.request_id = request_id

    def to_dict(self) -> dict[str, str]:
        return {"code": self.code, "message": self.message}


class SdkConfigurationError(SdkError):
    """The SDK was constructed with invalid or conflicting configuration."""

    code = "sdk.config"


class AuthenticationError(SdkError):
    """Authentication failed (missing, empty, or rejected credentials)."""

    code = "sdk.auth"


class AuthorizationError(SdkError):
    """Authenticated but not permitted for the requested operation."""

    code = "sdk.authorization"


class SdkTimeoutError(SdkError):
    """A request exceeded its configured timeout."""

    code = "sdk.timeout"


class SdkRetryExhaustedError(SdkError):
    """A transiently failing request exhausted its retry budget."""

    code = "sdk.retry_exhausted"


class SdkValidationError(SdkError):
    """The outgoing request was malformed and rejected before transport."""

    code = "sdk.validation"


class TransportError(SdkError):
    """The transport could not complete the request (connect, parse, HTTP)."""

    code = "sdk.transport"


class ApiError(SdkError):
    """The server responded with a non-2xx status.

    ``http_status`` and the server's ``api_code`` are carried for callers that
    need to branch on the remote failure class.
    """

    code = "sdk.api"

    def __init__(
        self,
        message: str,
        *,
        http_status: int,
        api_code: str | None = None,
        request_id: str | None = None,
    ) -> None:
        super().__init__(message, request_id=request_id)
        self.http_status = http_status
        self.api_code = api_code or self.code

    def to_dict(self) -> dict[str, str | int]:
        return {
            "code": self.api_code or self.code,
            "message": self.message,
            "http_status": self.http_status,
        }


__all__ = [
    "ApiError",
    "AuthenticationError",
    "AuthorizationError",
    "SdkConfigurationError",
    "SdkError",
    "SdkRetryExhaustedError",
    "SdkTimeoutError",
    "SdkValidationError",
    "TransportError",
]