"""Authentication for the AURA SDK.

The SDK never stores raw credentials in a form that leaks into logs or
serialized state. An authenticator owns the key/token and exposes only the
HTTP ``Authorization`` header value and a masked description.

``AnonymousAuthenticator`` sends no credentials (used against servers without
an API key configured). ``ApiKeyAuthenticator`` rejects keys shorter than 8
characters with a clear error.
"""

from __future__ import annotations

from .errors import AuthenticationError, SdkConfigurationError


class Authenticator:
    """Base authenticator. Subclasses implement :meth:`authorization_header`."""

    def authorization_header(self) -> str | None:
        raise NotImplementedError

    def describe(self) -> str:
        return "anonymous"


class AnonymousAuthenticator(Authenticator):
    """No credentials. Only valid against servers that do not require a key."""

    def authorization_header(self) -> str | None:
        return None

    def describe(self) -> str:
        return "anonymous"


class ApiKeyAuthenticator(Authenticator):
    """Bearer-token authenticator. The raw key is never rendered."""

    def __init__(self, api_key: str) -> None:
        if not api_key or len(api_key) < 8:
            raise AuthenticationError(
                "api key must be provided and at least 8 characters long; refusing to send a weak key"
            )
        self._key = api_key

    def authorization_header(self) -> str:
        return f"Bearer {self._key}"

    def describe(self) -> str:
        return f"api-key(****{self._key[-4:]})"


def authenticator_for(api_key: str | None) -> Authenticator:
    """Construct the right authenticator; ``None`` maps to anonymous."""
    if api_key is None:
        return AnonymousAuthenticator()
    try:
        return ApiKeyAuthenticator(api_key)
    except AuthenticationError as exc:
        raise SdkConfigurationError(exc.message) from exc


__all__ = ["AnonymousAuthenticator", "ApiKeyAuthenticator", "Authenticator", "authenticator_for"]