"""Smoke test for Phase 3 memory subsystem implementations."""

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
    working_pkg = load_package("aura_memory.working_memory", ROOT / "working_memory")
    episodic_pkg = load_package("aura_memory.episodic_memory", ROOT / "episodic_memory")
    semantic_pkg = load_package("aura_memory.semantic_memory", ROOT / "semantic_memory")
    associative_pkg = load_package("aura_memory.associative_memory", ROOT / "associative_memory")

    engine_mod = load_module("aura_memory.working_memory.engine", ROOT / "working_memory" / "engine.py")
    manager_mod = load_module("aura_memory.working_memory.manager", ROOT / "working_memory" / "manager.py")
    repo_mod = load_module("aura_memory.working_memory.repository", ROOT / "working_memory" / "repository.py")
    models_mod = load_module("aura_memory.working_memory.models", ROOT / "working_memory" / "models.py")
    schemas_mod = load_module("aura_memory.working_memory.schemas", ROOT / "working_memory" / "schemas.py")
    service_mod = load_module("aura_memory.working_memory.service", ROOT / "working_memory" / "service.py")

    episodic_engine_mod = load_module("aura_memory.episodic_memory.engine", ROOT / "episodic_memory" / "engine.py")
    episodic_manager_mod = load_module("aura_memory.episodic_memory.manager", ROOT / "episodic_memory" / "manager.py")
    episodic_repo_mod = load_module("aura_memory.episodic_memory.episode_repository", ROOT / "episodic_memory" / "episode_repository.py")
    episodic_models_mod = load_module("aura_memory.episodic_memory.models", ROOT / "episodic_memory" / "models.py")
    episodic_schemas_mod = load_module("aura_memory.episodic_memory.schemas", ROOT / "episodic_memory" / "schemas.py")
    episodic_service_mod = load_module("aura_memory.episodic_memory.service", ROOT / "episodic_memory" / "service.py")

    semantic_engine_mod = load_module("aura_memory.semantic_memory.engine", ROOT / "semantic_memory" / "engine.py")
    semantic_manager_mod = load_module("aura_memory.semantic_memory.manager", ROOT / "semantic_memory" / "manager.py")
    semantic_repo_mod = load_module("aura_memory.semantic_memory.repository", ROOT / "semantic_memory" / "repository.py")
    semantic_models_mod = load_module("aura_memory.semantic_memory.models", ROOT / "semantic_memory" / "models.py")
    semantic_schemas_mod = load_module("aura_memory.semantic_memory.schemas", ROOT / "semantic_memory" / "schemas.py")
    semantic_service_mod = load_module("aura_memory.semantic_memory.service", ROOT / "semantic_memory" / "service.py")

    associative_engine_mod = load_module("aura_memory.associative_memory.engine", ROOT / "associative_memory" / "engine.py")
    associative_manager_mod = load_module("aura_memory.associative_memory.manager", ROOT / "associative_memory" / "manager.py")
    associative_repo_mod = load_module("aura_memory.associative_memory.repository", ROOT / "associative_memory" / "repository.py")
    associative_models_mod = load_module("aura_memory.associative_memory.models", ROOT / "associative_memory" / "models.py")
    associative_schemas_mod = load_module("aura_memory.associative_memory.schemas", ROOT / "associative_memory" / "schemas.py")
    associative_service_mod = load_module("aura_memory.associative_memory.service", ROOT / "associative_memory" / "service.py")

    engine = engine_mod.Engine()
    engine.start()
    assert engine.process({"task": "store"})["cycle_count"] == 1
    assert engine.health()["active"] is True

    manager = manager_mod.Manager()
    manager.register("focus", {"priority": 1})
    assert manager.get("focus")["priority"] == 1

    repo = repo_mod.RepositoryRepository(ttl_seconds=60)
    repo.save("item", {"value": 42})
    assert repo.load("item")["value"] == 42
    assert repo.delete("item") is True

    model = models_mod.ModelsModel(name="topic")
    assert model.to_dict()["name"] == "topic"

    schema = schemas_mod.SchemasModel(name="context")
    assert schema.to_dict()["name"] == "context"

    service = service_mod.Service()
    service.start()
    assert service.execute({"event": "update"})["status"] == "ok"

    episodic_engine = episodic_engine_mod.Engine()
    episodic_engine.start()
    assert episodic_engine.process({"episode": "start"})["episodes_processed"] == 1

    episodic_manager = episodic_manager_mod.Manager()
    episodic_manager.register("session", {"active": True})
    assert episodic_manager.get("session")["active"] is True

    episodic_repo = episodic_repo_mod.EpisodeRepositoryRepository(ttl_seconds=60)
    episodic_repo.save("episode1", {"story": "begin"})
    assert episodic_repo.load("episode1")["story"] == "begin"

    episodic_model = episodic_models_mod.ModelsModel(name="memory")
    assert episodic_model.to_dict()["name"] == "memory"

    episodic_schema = episodic_schemas_mod.SchemasModel(name="episode_schema")
    assert episodic_schema.to_dict()["name"] == "episode_schema"

    episodic_service = episodic_service_mod.Service()
    episodic_service.start()
    assert episodic_service.execute({"phase": "3"})["status"] == "ok"

    semantic_engine = semantic_engine_mod.Engine()
    semantic_engine.start()
    assert semantic_engine.process({"meaning": "test"})["status"] == "processed"

    semantic_manager = semantic_manager_mod.Manager()
    semantic_manager.register("topic", {"weight": 0.8})
    assert semantic_manager.get("topic")["weight"] == 0.8

    semantic_repo = semantic_repo_mod.RepositoryRepository(ttl_seconds=60)
    semantic_repo.save("item", {"value": "semantic"})
    assert semantic_repo.load("item")["value"] == "semantic"

    semantic_model = semantic_models_mod.ModelsModel(name="meaning")
    assert semantic_model.to_dict()["name"] == "meaning"

    semantic_schema = semantic_schemas_mod.SchemasModel(name="semantic_schema")
    assert semantic_schema.to_dict()["name"] == "semantic_schema"

    semantic_service = semantic_service_mod.Service()
    semantic_service.start()
    assert semantic_service.execute({"intent": "understand"})["status"] == "ok"

    associative_engine = associative_engine_mod.Engine()
    associative_engine.start()
    assert associative_engine.process({"link": "a->b"})["status"] == "processed"

    associative_manager = associative_manager_mod.Manager()
    associative_manager.register("link", {"strength": 9})
    assert associative_manager.get("link")["strength"] == 9

    associative_repo = associative_repo_mod.RepositoryRepository(ttl_seconds=60)
    associative_repo.save("link1", {"value": "associate"})
    assert associative_repo.load("link1")["value"] == "associate"

    associative_model = associative_models_mod.ModelsModel(name="relation")
    assert associative_model.to_dict()["name"] == "relation"

    associative_schema = associative_schemas_mod.SchemasModel(name="associate_schema")
    assert associative_schema.to_dict()["name"] == "associate_schema"

    associative_service = associative_service_mod.Service()
    associative_service.start()
    assert associative_service.execute({"intent": "link"})["status"] == "ok"

    print("Phase 3 memory smoke test passed")


if __name__ == "__main__":
    main()
