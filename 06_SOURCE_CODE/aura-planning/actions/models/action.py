from __future__ import annotations
from dataclasses import dataclass, field
from .action_outcome import ActionOutcome

@dataclass(frozen=True, slots=True)
class Action:
    action_id: str
    name: str
    preconditions: tuple = ()
    effects: tuple = ()
    cost: float = 0.0
    duration: float = 0.0
    resources: tuple = ()
    risk: float = 0.0
    reversible: bool = False
    outcome_probability: float = 1.0
    metadata: dict = field(default_factory=dict)

    def __post_init__(self):
        if self.cost < 0 or self.duration < 0: raise ValueError("cost and duration must be non-negative")
        if not 0 <= self.risk <= 1 or not 0 <= self.outcome_probability <= 1:
            raise ValueError("risk and outcome_probability must be [0,1]")

    def is_applicable(self, state):
        return all(p.evaluate(state) for p in self.preconditions)

    def apply(self, state):
        if not self.is_applicable(state):
            return ActionOutcome(False, state, "precondition_failed", self)
        next_state = state
        for effect in self.effects:
            next_state = effect.apply(next_state)
        return ActionOutcome(True, next_state, None, self)
