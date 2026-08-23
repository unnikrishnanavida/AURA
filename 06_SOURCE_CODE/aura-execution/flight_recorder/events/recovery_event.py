from dataclasses import dataclass
@dataclass(frozen=True)
class RecoveryEvent:
    strategy:str
    reason:str
