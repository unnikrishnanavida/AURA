from dataclasses import dataclass
@dataclass(frozen=True, slots=True)
class ResourceRequirement:
    resource: str
    amount: float
    def __post_init__(self):
        if self.amount < 0:
            raise ValueError("resource requirement cannot be negative")
