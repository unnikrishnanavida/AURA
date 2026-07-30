from dataclasses import dataclass


@dataclass
class Identity:
    id: str
    name: str | None = None
