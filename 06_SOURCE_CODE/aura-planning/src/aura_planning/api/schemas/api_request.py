from dataclasses import dataclass, field
@dataclass(frozen=True, slots=True)
class ApiRequest:
    operation: str
    payload: dict = field(default_factory=dict)
    request_id: str | None = None
    def validate(self):
        if not self.operation.strip(): raise ValueError("operation is required")
        if not isinstance(self.payload, dict): raise TypeError("payload must be a mapping")
