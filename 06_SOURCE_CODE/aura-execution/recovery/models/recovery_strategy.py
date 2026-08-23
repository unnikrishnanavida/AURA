from dataclasses import dataclass
@dataclass(frozen=True)
class RecoveryStrategy:
    name:str
    max_attempts:int=0
