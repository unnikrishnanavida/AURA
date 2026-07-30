from dataclasses import dataclass


@dataclass
class ReleaseMetadata:
    version: str
    notes: str | None = None
