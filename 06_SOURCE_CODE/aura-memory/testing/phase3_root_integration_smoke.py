"""Root-level Phase 3 integration smoke test for AURA Memory."""

from __future__ import annotations

import importlib.util
import pathlib
import sys
import types

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCRIPT_DIR = pathlib.Path(__file__).resolve().parent

for entry in list(sys.path):
    try:
        if pathlib.Path(entry).resolve() == SCRIPT_DIR:
            sys.path.remove(entry)
    except Exception:
        continue


def ensure_package(package_name: str, package_path: pathlib.Path):
    pkg = types.ModuleType(package_name)
    pkg.__path__ = [str(package_path)]
    sys.modules[package_name] = pkg
    return pkg


def load_package(package_name: str, package_dir: pathlib.Path):
    init_path = package_dir / "__init__.py"
    spec = importlib.util.spec_from_file_location(
        package_name,
        init_path,
        submodule_search_locations=[str(package_dir)],
    )
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[package_name] = module
    spec.loader.exec_module(module)
    return module


def main() -> None:
    ensure_package("aura_memory", ROOT)
    aura_pkg = load_package("aura_memory", ROOT)
    working_pkg = load_package("aura_memory.working_memory", ROOT / "working_memory")
    episodic_pkg = load_package("aura_memory.episodic_memory", ROOT / "episodic_memory")
    semantic_pkg = load_package("aura_memory.semantic_memory", ROOT / "semantic_memory")
    associative_pkg = load_package("aura_memory.associative_memory", ROOT / "associative_memory")

    assert hasattr(aura_pkg, "__path__")
    assert working_pkg.__name__ == "aura_memory.working_memory"
    assert episodic_pkg.__name__ == "aura_memory.episodic_memory"
    assert semantic_pkg.__name__ == "aura_memory.semantic_memory"
    assert associative_pkg.__name__ == "aura_memory.associative_memory"

    # Sanity check one root-level component import
    core_pkg = load_package("aura_memory.core", ROOT / "core")
    assert hasattr(core_pkg, "APP_VERSION")

    print("Phase 3 root integration smoke test passed")


if __name__ == "__main__":
    main()
