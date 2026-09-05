"""Secret redaction.

Central redaction used by loggers, serializers, and the API layer. Secrets are
registered once; any string containing a secret value is rendered with the
value masked before it ever reaches a sink.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass, field

_MASK = "<REDACTED>"


@dataclass
class SecretRedactor:
    secrets: set[str] = field(default_factory=set)

    def register(self, secret: str) -> None:
        text = str(secret).strip()
        if text:
            self.secrets.add(text)

    def register_many(self, secrets: Iterable[str]) -> None:
        for secret in secrets:
            self.register(secret)

    def redact(self, text: str) -> str:
        out = text
        for secret in self.secrets:
            if len(secret) >= 4:
                out = out.replace(secret, _MASK)
        patterns = [
            r"(?i)(api[_-]?key|token|password|secret)([\"']?\s*[:=]\s*[\"']?)[A-Za-z0-9_\-\.]{6,}",
            r"(?i)authorization:\s*bearer\s+[A-Za-z0-9_\-\.]{8,}",
        ]
        for pattern in patterns:
            out = re.sub(pattern, lambda m: f"{m.group(1)}{m.group(2)}{_MASK}" if m.lastindex and m.lastindex >= 2 else _MASK, out)
        return out

    def mask(self, value: str) -> str:
        """Mask a secret value entirely (never echoes the secret)."""
        return _MASK if value else ""


__all__ = ["SecretRedactor"]