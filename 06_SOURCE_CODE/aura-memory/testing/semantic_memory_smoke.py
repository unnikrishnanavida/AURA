"""Smoke test for the semantic memory subsystem."""

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
    semantic_pkg = load_package("aura_memory.semantic_memory", ROOT / "semantic_memory")
    engine_mod = load_module("aura_memory.semantic_memory.engine", ROOT / "semantic_memory" / "engine.py")
    manager_mod = load_module("aura_memory.semantic_memory.manager", ROOT / "semantic_memory" / "manager.py")
    repository_mod = load_module("aura_memory.semantic_memory.repository", ROOT / "semantic_memory" / "repository.py")
    service_mod = load_module("aura_memory.semantic_memory.service", ROOT / "semantic_memory" / "service.py")
    models_mod = load_module("aura_memory.semantic_memory.models", ROOT / "semantic_memory" / "models.py")
    schemas_mod = load_module("aura_memory.semantic_memory.schemas", ROOT / "semantic_memory" / "schemas.py")
    storage_mod = load_module("aura_memory.semantic_memory.storage", ROOT / "semantic_memory" / "storage.py")

    engine = engine_mod.Engine()
    engine.start()
    result = engine.process({"text": "hello"})
    assert result["processed_count"] == 1
    assert engine.health()["processed_count"] == 1

    manager = manager_mod.Manager()
    manager.register("alpha", {"value": 1})
    assert manager.get("alpha")["value"] == 1

    repo = repository_mod.RepositoryRepository(ttl_seconds=60)
    repo.save("note", {"text": "hello"})
    assert repo.load("note")["text"] == "hello"
    assert repo.delete("note") is True

    service = service_mod.Service()
    service.start()
    assert service.execute({"kind": "semantic"})["status"] == "ok"

    model = models_mod.ModelsModel(name="thing")
    assert model.to_dict()["name"] == "thing"
    round_trip = models_mod.ModelsModel.from_dict(model.to_dict())
    assert round_trip.name == "thing"

    schema_model = schemas_mod.SchemasModel(name="schema")
    assert schema_model.to_dict()["name"] == "schema"

    storage = storage_mod.StorageRepository(ttl_seconds=60)
    storage.save("bucket", {"kind": "semantic"})
    assert storage.load("bucket")["kind"] == "semantic"

    print("Semantic memory smoke test passed")


if __name__ == "__main__":
    main()
