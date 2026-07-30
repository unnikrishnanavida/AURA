from __future__ import annotations

from typing import Dict, Optional


class SecretManager:
    """In-memory secret manager. Replace with vault-backed implementation in production."""

    def __init__(self) -> None:
        self._store: Dict[str, str] = {}

    def set(self, key: str, secret: str) -> None:
        self._store[key] = secret

    def get(self, key: str) -> Optional[str]:
        return self._store.get(key)
