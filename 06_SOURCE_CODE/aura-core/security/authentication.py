from __future__ import annotations

from typing import Optional


class Authenticator:
    def authenticate(self, username: str, password: str) -> Optional[dict]:
        """Authenticate a user; return principal dict on success."""
        # Placeholder for real auth (e.g., DB lookup, LDAP)
        return None
