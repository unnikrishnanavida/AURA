from dataclasses import dataclass, field
@dataclass(frozen=True, slots=True)
class PlanningSettings:
    planner: str = "a_star"
    max_depth: int = 100
    timeout_seconds: float = 30.0
    search_width: int = 32
    safety_mode: str = "strict"
    metadata: dict = field(default_factory=dict)
    def validate(self):
        if self.max_depth <= 0 or self.search_width <= 0 or self.timeout_seconds <= 0: raise ValueError("planning limits must be positive")
        if self.safety_mode not in {"strict","balanced","permissive"}: raise ValueError("invalid safety mode")
