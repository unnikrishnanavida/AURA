from dataclasses import dataclass, field
@dataclass(frozen=True, slots=True)
class ApiResponse:
    success: bool
    data: object = None
    error: object = None
    request_id: str | None = None
    metadata: dict = field(default_factory=dict)
    def as_dict(self):
        return {"success": self.success, "data": self.data, "error": self.error.as_dict() if hasattr(self.error, "as_dict") else self.error, "request_id": self.request_id, "metadata": self.metadata}
    @classmethod
    def ok(cls, data, request_id=None, **metadata): return cls(True, data, None, request_id, metadata)
    @classmethod
    def fail(cls, error, request_id=None, **metadata): return cls(False, None, error, request_id, metadata)
