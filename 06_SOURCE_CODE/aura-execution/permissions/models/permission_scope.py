from dataclasses import dataclass
@dataclass(frozen=True)
class PermissionScope:
    resource: str
    operations: frozenset[str]=frozenset()
    def allows(self,operation): return operation in self.operations or "*" in self.operations
