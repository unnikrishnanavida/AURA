from dataclasses import dataclass, field
@dataclass(frozen=True)
class ToolInput:
    values:dict=field(default_factory=dict)
