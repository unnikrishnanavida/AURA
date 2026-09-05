from dataclasses import dataclass
@dataclass(frozen=True, slots=True)
class ResourceAllocation:
    allocations: dict
    def amount(self, resource): return float(self.allocations.get(resource, 0))
