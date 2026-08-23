from dataclasses import dataclass
@dataclass(frozen=True)
class PlanConstraints:
    allowed_capabilities:frozenset=frozenset()
