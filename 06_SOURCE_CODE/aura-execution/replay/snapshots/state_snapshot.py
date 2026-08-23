from dataclasses import dataclass
@dataclass(frozen=True)
class StateSnapshot:
    values:dict
