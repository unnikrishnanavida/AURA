from dataclasses import dataclass
@dataclass(frozen=True,slots=True)
class ReplanningCase:
    name:str; request:object; expected_recovery:bool=True
