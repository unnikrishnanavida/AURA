from dataclasses import dataclass
@dataclass(frozen=True,slots=True)
class AdversarialCase:
    name:str; input:object; expected_rejection:bool=True
