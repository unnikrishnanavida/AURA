"""Logging helpers for aura-memory."""

import importlib.util
import pathlib
import sys
import sysconfig

try:
    from ..config.settings import load_settings
except ImportError:  # pragma: no cover - fallback for direct imports
    from config.settings import load_settings


def _load_stdlib_logging_module():
    module_name = "_stdlib_logging"
    if module_name in sys.modules:
        return sys.modules[module_name]
    stdlib_root = pathlib.Path(sysconfig.get_paths()["stdlib"])
    module_path = stdlib_root / "logging" / "__init__.py"
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module


def setup_logging(level: str | None = None) -> None:
    if level is None:
        settings = load_settings()
        level = settings.log_level
    logging_module = _load_stdlib_logging_module()
    logging_module.basicConfig(level=getattr(logging_module, level.upper(), logging_module.INFO))


__all__ = ["setup_logging"]
