from dataclasses import dataclass, field


@dataclass(frozen=True)
class Capability:
    name: str
    operations: frozenset[str]=frozenset()
    metadata: dict=field(default_factory=dict)
    def supports(self, operation): return operation in self.operations or "*" in self.operations
