from dataclasses import dataclass, field
@dataclass
class AuthorizationContext:
    principal: str
    scopes: set[str]=field(default_factory=set)
    approved: bool=False
