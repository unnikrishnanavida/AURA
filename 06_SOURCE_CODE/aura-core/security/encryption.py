from __future__ import annotations

try:
    from cryptography.fernet import Fernet  # type: ignore
except Exception:  # pragma: no cover - optional dependency
    Fernet = None


class EncryptionError(Exception):
    pass


class Encryptor:
    def __init__(self, key: bytes | None = None) -> None:
        if Fernet is None:
            raise EncryptionError("cryptography is not installed")
        self._key = key or Fernet.generate_key()
        self._fernet = Fernet(self._key)

    def encrypt(self, data: bytes) -> bytes:
        return self._fernet.encrypt(data)

    def decrypt(self, token: bytes) -> bytes:
        return self._fernet.decrypt(token)
