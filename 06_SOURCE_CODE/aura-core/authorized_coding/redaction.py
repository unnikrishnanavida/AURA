"""Secret redaction for the authorized-coding pipeline.

Self-contained implementation (stdlib only) so that :mod:`authorized_coding`
remains a dependency-free core package. It mirrors the existing
``aura.security.redaction.SecretRedactor`` contract but is scoped to
payloads and file-like values instead of free-form log lines.
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass, field

__all__ = ["SecretRedactor", "redact_payload"]

_MASK = "<REDACTED>"

# Regex fallbacks (mirrors the existing aura secret-patterns): any value
# whose shape matches a known credential carrier is masked.
_SECRET_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"(sk-[A-Za-z0-9_-]{6,})", re.IGNORECASE), _MASK),
    (re.compile(r"(api[_-]?key\s*[=:]?\s*[A-Za-z0-9_\-\.]{6,})", re.IGNORECASE), "api_key=<redacted>"),
    (re.compile(r"(token\s*[=:]?\s*[A-Za-z0-9_.-]{6,})", re.IGNORECASE), "token=<redacted>"),
    (re.compile(r"(bearer\s+[A-Za-z0-9_.-]{6,})", re.IGNORECASE), "bearer <redacted>"),
    (re.compile(r"(password\s*[=:]?\s*\S+)", re.IGNORECASE), "password=<redacted>"),
    (re.compile(r"(authorization\s*[=:]?\s*\S+)", re.IGNORECASE), "authorization=<redacted>"),
)


@dataclass
class SecretRedactor:
    """Masks known secrets and credential-like shapes in text or payloads."""

    secrets: set[str] = field(default_factory=set)

    def register(self, secret: str) -> None:
        text = str(secret).strip()
        if text:
            self.secrets.add(text)

    def register_many(self, secrets: Iterable[str]) -> None:
        for secret in secrets:
            self.register(secret)

    def redact(self, text: str) -> str:
        """Render *text* with every registered secret and credential-shaped
        substring replaced by a mask. The returned string never contains the
        original secret values."""
        out = text
        for secret in self.secrets:
            if len(secret) >= 4:
                out = out.replace(secret, _MASK)
        for pattern, replacement in _SECRET_PATTERNS:
            out = pattern.sub(replacement, out)
        return out

    def mask(self, value: str) -> str:
        """Mask a secret value entirely (never echo the secret)."""
        return _MASK if value else ""


def redact_payload(payload: dict[str, object], redactor: SecretRedactor) -> dict[str, object]:
    """Return a *copy* of *payload* where every secret-ish value is masked.

    The input *payload* is never mutated. Scalar values that exactly match a
    registered secret, or that match a credential-shaped regex, become the
    mask; nested mappings and sequences are walked recursively. Non-string
    values pass through unchanged.
    """
    out: dict[str, object] = {}
    for key, value in payload.items():
        if isinstance(value, str):
            out[key] = redactor.redact(value)
        elif isinstance(value, dict):
            out[key] = redact_payload(value, redactor)  # type: ignore[arg-type]
        elif isinstance(value, (list, tuple)):
            out[key] = [redactor.redact(item) if isinstance(item, str) else item for item in value]
        else:
            out[key] = value
    return out
