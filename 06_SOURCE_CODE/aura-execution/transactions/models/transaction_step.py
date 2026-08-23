from dataclasses import dataclass
@dataclass(frozen=True)
class TransactionStep:
    name:str
    action:object
    compensation:object|None=None
