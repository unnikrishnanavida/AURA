from dataclasses import dataclass
@dataclass(frozen=True, slots=True)
class SafetyPolicy:
    name: str
    rules: tuple
    default_deny: bool = True
    def evaluate(self, candidate):
        violations=tuple(rule(candidate) for rule in self.rules)
        return tuple(v for v in violations if v)
