from dataclasses import dataclass
@dataclass(frozen=True, slots=True)
class ApiError:
    code: str
    message: str
    details: dict = None
    status: int = 400
    def __post_init__(self):
        if self.status < 400 or self.status > 599: raise ValueError("invalid HTTP error status")
    def as_dict(self):
        return {"code": self.code, "message": self.message, "details": self.details or {}}
