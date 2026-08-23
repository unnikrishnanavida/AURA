from pathlib import Path

root = Path("aura_sdk")
assert root.exists(), f"Missing root: {root!r}"

template = '''"""AURA SDK {title} validator."""

from __future__ import annotations
from typing import Any


class Validator:
    """Core validator for aura_sdk.{package_name}."""

    def validate(self, data: Any) -> bool:
        """Return true when data is not None."""
        if data is None:
            raise ValueError("data cannot be None")
        return True
'''

count = 0
for path in sorted(root.rglob('*/validator.py')):
    title = path.parent.name.replace('_', ' ').title()
    package_name = path.parent.name
    path.write_text(template.format(title=title, package_name=package_name), encoding='utf-8')
    count += 1

print(f'Rewritten {count} validator files')
