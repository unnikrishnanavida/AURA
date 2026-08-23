from dataclasses import dataclass,field
@dataclass(frozen=True,slots=True)
class ReplanningRequest:
    original:object; observed_state:object; failure_reason:str|None=None; options:dict=field(default_factory=dict)
    def validate(self): self.original.validate()
