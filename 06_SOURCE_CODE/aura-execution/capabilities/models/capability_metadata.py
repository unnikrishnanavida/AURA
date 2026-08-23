from dataclasses import dataclass
@dataclass(frozen=True)
class CapabilityMetadata:
    provider: str
    version: str="1"
    reliability: float=1.0
