from __future__ import annotations

from typing import Any, Dict


class Validator:
    def validate(self, obj: Any, schema: Dict[str, Any]) -> bool:
        # placeholder: integrate with jsonschema or pydantic in real impl
        return True
