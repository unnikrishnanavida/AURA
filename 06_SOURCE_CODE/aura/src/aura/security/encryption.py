"""Encryption at rest / in motion for sensitive local and transport data.

Uses the established ``cryptography`` library (Fernet = AES-128-CBC + HMAC).
We never invent algorithms. Key management:

- key source: explicit ``AURA_DATA_KEY`` env var, a key file, or ``key`` param;
- weak/missing keys are rejected (no silent plaintext fallback);
- rotation is *prefix-based*: ``rotate_to(new_key)`` records the new key while
  the previous one remains valid for decryption of older ciphertexts.

This module is used (and tested) directly; wiring it into specific storage
fields is an operator decision for the sensitive subsets of data.
"""

from __future__ import annotations

import base64
import os
from dataclasses import dataclass

from cryptography.fernet import Fernet, InvalidToken

from aura.foundation.errors import ConfigurationError

_MIN_KEY_LEN = 32


@dataclass
class Ciphertext:
    token: str
    key_id: str


class FernetCipher:
    """Encrypt/decrypt strings with prefix-based key rotation support."""

    def __init__(self, keys: list[str] | None = None, *, key: str | None = None, key_id: str = "k1") -> None:
        """Provide one or more keys (oldest first for rotation); ``key`` adds/selects the active key.

        Keys are URL-safe base64 32-byte Fernet keys; a plain 32+ char string is
        derived deterministically (SHA-256) to a Fernet key.
        """
        self._rotations: list[tuple[str, Fernet]] = []
        self._active_key_id = key_id
        if keys:
            for index, raw in enumerate(keys):
                self._rotations.append((f"k{index + 1}", _fernet_from(raw)))
        if key:
            self._rotations.append((key_id, _fernet_from(key)))
            self._active_key_id = key_id
        if not self._rotations:
            raise ConfigurationError("encryption requires at least one key (set AURA_DATA_KEY)")

    @classmethod
    def from_env(cls) -> FernetCipher:
        raw = os.environ.get("AURA_DATA_KEY", "")
        if not raw:
            raise ConfigurationError("AURA_DATA_KEY is not set; refusing unencrypted operation")
        return cls(key=raw)

    def encrypt(self, plaintext: str) -> Ciphertext:
        active = self._rotations[-1][1]
        token = active.encrypt(plaintext.encode("utf-8")).decode("ascii")
        return Ciphertext(token=token, key_id=self._active_key_id)

    def decrypt(self, ciphertext: Ciphertext) -> str:
        last_error: Exception | None = None
        for _, fernet in self._rotations:
            try:
                return fernet.decrypt(ciphertext.token.encode("ascii")).decode("utf-8")
            except InvalidToken as exc:
                last_error = exc
        raise ConfigurationError(
            f"failed to decrypt token with any known key ({last_error})"
        )

    def rotate_to(self, new_key: str, *, new_key_id: str = "k-current") -> None:
        """Add a new active key; the old key stays valid for decryption."""
        self._rotations.append((new_key_id, _fernet_from(new_key)))
        self._active_key_id = new_key_id

    def key_ids(self) -> list[str]:
        return [kid for kid, _ in self._rotations]


def _fernet_from(raw: str) -> Fernet:
    """Coerce a key string to a Fernet key (32-byte urlsafe b64 or derived)."""
    candidate = raw.encode("utf-8")
    try:
        decoded = base64.urlsafe_b64decode(candidate)
        if len(decoded) == _MIN_KEY_LEN:
            return Fernet(raw)
    except Exception:  # noqa: BLE001 - fall through to derivation
        pass
    if len(candidate) < _MIN_KEY_LEN:
        raise ConfigurationError("encryption key must be a 32-byte urlsafe base64 key or >= 32 chars")
    import hashlib

    derived = base64.urlsafe_b64encode(hashlib.sha256(candidate).digest())
    return Fernet(derived.decode("ascii"))


__all__ = ["Ciphertext", "FernetCipher"]