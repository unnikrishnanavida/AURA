from dataclasses import dataclass
@dataclass(frozen=True)
class CapabilityRequirement:
    name: str
    operation: str
