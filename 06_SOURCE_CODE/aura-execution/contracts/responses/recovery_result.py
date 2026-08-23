from dataclasses import dataclass
@dataclass
class RecoveryResult:
    recovered: bool
    strategy: str
    reason: str
