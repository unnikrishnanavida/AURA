from __future__ import annotations

from dataclasses import dataclass


@dataclass
class Certificate:
    subject: str
    issuer: str
    data: bytes
