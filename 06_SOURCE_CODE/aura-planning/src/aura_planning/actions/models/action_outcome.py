from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class ActionOutcome:
    success: bool
    state: object
    reason: str | None
    action: object
