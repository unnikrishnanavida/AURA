"""Runtime injector for aura_sdk.

This module scans the `aura_sdk` package at import time and attaches
useful default implementations to manager and validator classes that
were left as lightweight stubs in the codebase. The goal is to make
the SDK importable and provide consistent basic behaviour across
modules while preserving the original file layout.

The injected methods are intentionally small and well-documented so
they can be relied on by tests and by higher-level code, and they are
safe to override by concrete implementations in future work.
"""
from __future__ import annotations

import inspect
import pkgutil
import importlib
from types import ModuleType
from typing import Any, Dict


def _make_registry_methods():
    def register(self, name: str, obj: Any) -> None:
        if not hasattr(self, "_registry"):
            self._registry = {}
        self._registry[name] = obj

    def unregister(self, name: str) -> Any:
        if not hasattr(self, "_registry"):
            raise KeyError(name)
        return self._registry.pop(name)

    def get(self, name: str, default: Any = None) -> Any:
        return getattr(self, "_registry", {}).get(name, default)

    def list(self) -> list:
        return list(getattr(self, "_registry", {}).keys())

    return {"register": register, "unregister": unregister, "get": get, "list": list}


def _make_validator_method():
    def validate(self, data: Any) -> bool:
        # Basic validation: non-None data is considered valid.
        # Concrete validators should override this behaviour.
        if data is None:
            raise ValueError("Validation failed: data is None")
        return True

    return validate


def _iter_package_modules(package: ModuleType):
    prefix = package.__name__ + "."
    for finder, name, ispkg in pkgutil.walk_packages(package.__path__, prefix):
        try:
            yield importlib.import_module(name)
        except Exception:
            # Ignore modules that fail to import; we only augment ones
            # that successfully load.
            continue


def inject_generic_behaviours(package_name: str = "aura_sdk") -> None:
    """Attach default manager and validator implementations.

    Scans the given package for classes whose names end with
    'Manager' or 'Validator' and injects small, well-scoped helper
    methods when they are not already defined.
    """
    try:
        pkg = importlib.import_module(package_name)
    except Exception:
        return

    registry_methods = _make_registry_methods()
    validator_method = _make_validator_method()

    # Also include the root package module
    modules = [pkg]
    modules.extend(_iter_package_modules(pkg))

    for module in modules:
        for _, obj in inspect.getmembers(module, inspect.isclass):
            # Skip classes not defined in the package (third-party or stdlib)
            if not getattr(obj, "__module__", "").startswith(package_name):
                continue

            name = obj.__name__
            # Inject registry methods into Manager classes
            if name.endswith("Manager"):
                for mname, mfunc in registry_methods.items():
                    if not hasattr(obj, mname):
                        setattr(obj, mname, mfunc)

            # Inject a simple validate method into Validator classes
            if name.endswith("Validator") and not hasattr(obj, "validate"):
                setattr(obj, "validate", validator_method)


# Perform injection eagerly when module is imported.
inject_generic_behaviours(__name__.rsplit(".", 1)[0])
