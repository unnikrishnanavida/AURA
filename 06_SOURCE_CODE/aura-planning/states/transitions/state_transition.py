from dataclasses import dataclass

@dataclass(frozen=True, slots=True)
class StateTransition:
    before: object
    after: object
    action_id: str
    cost: float = 0.0
    duration: float = 0.0

    @property
    def changed(self):
        a = getattr(self.before, "values", self.before)
        b = getattr(self.after, "values", self.after)
        return {k: (a.get(k), b.get(k)) for k in set(a) | set(b) if a.get(k) != b.get(k)}
