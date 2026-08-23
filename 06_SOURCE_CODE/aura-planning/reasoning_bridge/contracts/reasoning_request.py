from dataclasses import dataclass, field
@dataclass(frozen=True, slots=True)
class ReasoningRequest:
    problem: object
    context: object = None
    constraints: tuple = ()
    metadata: dict = field(default_factory=dict)
    def validate(self):
        if self.problem is None:
            raise ValueError("problem is required")
