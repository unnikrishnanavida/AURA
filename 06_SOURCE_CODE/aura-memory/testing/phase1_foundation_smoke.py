"""Smoke test for the Phase 1 foundation package surface."""

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


def load_module(module_name: str, file_path: pathlib.Path):
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def main() -> None:
    ensure_package("aura_memory", ROOT)
    core = load_package("aura_memory.core", ROOT / "core")
    config = load_package("aura_memory.config", ROOT / "config")
    load_module("aura_memory.config.settings", ROOT / "config" / "settings.py")
    serialization = load_package("aura_memory.serialization", ROOT / "serialization")
    logging_pkg = load_package("aura_memory.logging", ROOT / "logging")
    telemetry = load_package("aura_memory.telemetry", ROOT / "telemetry")
    validation = load_package("aura_memory.validation", ROOT / "validation")
    utilities = load_package("aura_memory.utilities", ROOT / "utilities")
    identifiers = load_package("aura_memory.identifiers", ROOT / "identifiers")
    events = load_package("aura_memory.events", ROOT / "events")
    di = load_package("aura_memory.di", ROOT / "di")
    concurrency = load_package("aura_memory.concurrency", ROOT / "concurrency")
    lifecycle = load_package("aura_memory.lifecycle", ROOT / "lifecycle")
    versioning = load_package("aura_memory.versioning", ROOT / "versioning")
    security = load_package("aura_memory.security", ROOT / "security")
    network = load_package("aura_memory.network", ROOT / "network")

    assert core.APP_VERSION
    assert config.load_settings().app_name == "aura_memory"
    assert serialization.safe_dumps({"ok": True})
    logging_pkg.setup_logging("debug")
    telemetry.init_telemetry(False)
    assert validation.dump_schema({"required": ["id"]})
    assert utilities.BaseModel.__name__ == "BaseModel"
    assert identifiers.new_id()
    events.publish("test", {"ok": True})
    di.register("sample", lambda: {"ok": True})
    assert di.resolve("sample")["ok"] is True
    assert concurrency.run_blocking(lambda: 42) == 42
    lifecycle.register_shutdown(lambda: None)
    lifecycle.shutdown()
    assert versioning.get_version() == core.APP_VERSION
    assert security.sanitize_text("<b>") == "&lt;b&gt;"
    assert network.resolve_hostname("localhost") in {"127.0.0.1", "localhost"}

    print("Phase 1 foundation smoke test passed")


if __name__ == "__main__":
    main()
