from dataclasses import dataclass
@dataclass(frozen=True,slots=True)
class ResourceSnapshot:
    resources:dict
    @classmethod
    def capture(cls,resources): return cls(dict(resources))
