"""Simple auth helpers."""

from __future__ import annotations

import hmac
import hashlib
from typing import Optional


def verify_signature(secret: str, message: str, signature: str) -> bool:
    expected = hmac.new(secret.encode(), message.encode(), hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, signature)


def sign_message(secret: str, message: str) -> str:
    return hmac.new(secret.encode(), message.encode(), hashlib.sha256).hexdigest()


__all__ = ["verify_signature", "sign_message"]
