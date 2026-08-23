from dataclasses import dataclass, field
@dataclass(frozen=True, slots=True)
class Resource:
    name: str
    capacity: float
    unit: str = "unit"
    metadata: dict = field(default_factory=dict)
    def __post_init__(self):
        if self.capacity < 0:
            raise ValueError("resource capacity cannot be negative")
