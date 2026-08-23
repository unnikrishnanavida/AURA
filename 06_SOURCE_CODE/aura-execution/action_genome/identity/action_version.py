from dataclasses import dataclass
@dataclass(frozen=True)
class ActionVersion:
    major:int=1;minor:int=0
