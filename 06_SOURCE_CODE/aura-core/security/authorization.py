from __future__ import annotations

from typing import Dict, Any


class Authorizer:
    def is_allowed(self, principal: Dict[str, Any], action: str, resource: str) -> bool:
        return False
