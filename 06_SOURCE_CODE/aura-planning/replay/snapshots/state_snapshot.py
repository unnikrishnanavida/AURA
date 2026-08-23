from dataclasses import dataclass
@dataclass(frozen=True,slots=True)
class StateSnapshot:
    values:dict
    @classmethod
    def capture(cls,state): return cls(dict(getattr(state,"values",state)))
