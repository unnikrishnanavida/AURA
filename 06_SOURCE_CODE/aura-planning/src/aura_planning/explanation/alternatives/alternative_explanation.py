from dataclasses import dataclass
@dataclass(frozen=True,slots=True)
class AlternativeExplanation:
    alternative:object; reason:str; score:float
