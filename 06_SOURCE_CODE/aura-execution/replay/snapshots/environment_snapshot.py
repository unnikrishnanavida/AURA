from dataclasses import dataclass
@dataclass(frozen=True)
class EnvironmentSnapshot:
    capabilities:tuple
    tools:tuple
