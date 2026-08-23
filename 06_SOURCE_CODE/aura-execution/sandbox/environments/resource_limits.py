from dataclasses import dataclass
@dataclass(frozen=True)
class ResourceLimits:
    cpu_seconds:float=30
    memory_mb:int=256
    files:int=100
