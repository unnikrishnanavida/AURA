from dataclasses import dataclass
@dataclass(frozen=True)
class Permission:
    name: str
    effect: str="allow"
    scope: str="*"
