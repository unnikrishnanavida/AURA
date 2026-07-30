from dataclasses import dataclass


@dataclass
class SemanticVersion:
    major: int = 0
    minor: int = 1
    patch: int = 0

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}.{self.patch}"
