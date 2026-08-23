from dataclasses import dataclass
@dataclass(frozen=True)
class StateChange:
    key:str
    before:object
    after:object
