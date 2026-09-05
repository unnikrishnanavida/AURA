"""Import validation gate.

Imports every public module in :mod:`aura` to catch broken relative imports,
circular imports, and missing dependencies before CI proceeds.

Run:  python scripts/validate_imports.py
"""

from __future__ import annotations

import importlib
import pathlib
import sys
from typing import Final

ROOT: Final = pathlib.Path(__file__).resolve().parents[1]
PKG: Final = ROOT / "src"
PACKAGE_NAME: Final = "aura"


def discover_modules(package_dir: pathlib.Path, package: str) -> list[str]:
    """Return every importable submodule name under *package_dir*."""
    modules = [package]
    seen = {package}
    for path in sorted(package_dir.rglob("*.py")):
        if path.name == "__init__.py":
            rel = path.parent.relative_to(package_dir)
            if rel == pathlib.Path("."):
                continue  # the package's own __init__ already listed
            module = f"{package}.{rel.as_posix().replace('/', '.')}"
        else:
            rel = path.relative_to(package_dir).with_suffix("")
            module = f"{package}.{rel.as_posix().replace('/', '.')}"
        if module not in seen:
            modules.append(module)
            seen.add(module)
    return sorted(modules)


def main() -> int:
    """Import every module and report failures."""
    PKG_LOCATION = str(PKG)
    if PKG_LOCATION not in sys.path:
        sys.path.insert(0, PKG_LOCATION)

    modules = discover_modules(PKG / PACKAGE_NAME, PACKAGE_NAME)
    failed: list[str] = []
    for module in modules:
        try:
            importlib.import_module(module)
        except Exception as exc:  # noqa: BLE001 - report whatever broke
            failed.append(f"{module}: {type(exc).__name__}: {exc}")

    print(f"importing {len(modules) - len(failed)}/{len(modules)} modules ok")
    if failed:
        print("FAILED:")
        for entry in failed:
            print(f"  {entry}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())