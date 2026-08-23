"""Import and circular-dependency validation.

Walks every module under ``aura_agent``, imports it, and fails loudly if any
module cannot be imported (signaling a circular import or broken reference).
"""

from __future__ import annotations

import importlib
import pkgutil
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import aura_agent  # noqa: F401


def main() -> int:
    failures: list[str] = []
    count = 0
    for mod in sorted(
        pkgutil.walk_packages(aura_agent.__path__, prefix="aura_agent."),
        key=lambda m: m.name,
    ):
        try:
            importlib.import_module(mod.name)
            count += 1
        except Exception as exc:  # noqa: BLE001 - aggregate all import failures
            failures.append(f"{mod.name}: {exc}")
    if failures:
        print("IMPORT FAILURES:")
        for f in failures:
            print(f"  {f}")
        return 1
    print(f"All {count} modules import cleanly (no circular imports).")
    return 0


if __name__ == "__main__":
    sys.exit(main())