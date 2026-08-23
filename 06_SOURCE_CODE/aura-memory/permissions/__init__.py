"""Permissions and API key authorization for aura-memory."""

from __future__ import annotations

import os
from typing import Dict, Iterable, List, Optional


class AuthorizationError(Exception):
    pass


class PermissionStore:
    def __init__(self, default_api_key: Optional[str] = None) -> None:
        self._keys: Dict[str, List[str]] = {}
        self._permissions: Dict[str, List[str]] = {
            "read": ["reader", "writer", "admin"],
            "write": ["writer", "admin"],
            "delete": ["admin"],
        }
        api_key = default_api_key or os.getenv("AURA_API_KEY")
        if api_key:
            self.register_api_key(api_key, ["admin"])

    def register_api_key(self, key: str, roles: Iterable[str]) -> None:
        self._keys[key] = list(roles)

    def roles_for(self, key: str) -> List[str]:
        return self._keys.get(key, [])

    def has_permission(self, key: str, operation: str) -> bool:
        if key not in self._keys:
            return False
        roles = set(self.roles_for(key))
        allowed = set(self._permissions.get(operation, []))
        return bool(roles & allowed)

    def authorize(self, key: str, operation: str) -> None:
        if not self.has_permission(key, operation):
            raise AuthorizationError(f"API key does not permit '{operation}'")


_default_store = PermissionStore()


def get_default_permission_store() -> PermissionStore:
    return _default_store


__all__ = ["AuthorizationError", "PermissionStore", "get_default_permission_store"]
