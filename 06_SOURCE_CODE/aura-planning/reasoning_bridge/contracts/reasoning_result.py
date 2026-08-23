from dataclasses import dataclass, field
@dataclass(frozen=True, slots=True)
class ReasoningResult:
    conclusion: object
    confidence: float
    evidence: tuple = ()
    trace_id: str | None = None
    metadata: dict = field(default_factory=dict)
    def __post_init__(self):
        if not 0 <= self.confidence <= 1:
            raise ValueError("confidence must be in [0, 1]")
