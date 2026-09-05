"""Layered configuration loading with startup validation.

Load order (later layers win):
  1. built-in defaults
  2. YAML/JSON file at `AURA_CONFIG` or an explicit path
  3. environment variables prefixed with `AURA_`
"""

from __future__ import annotations

import json
import os
from collections.abc import Mapping
from pathlib import Path
from typing import Any, cast

import yaml

from aura.config.settings import AuraConfig, Environments
from aura.foundation.errors import ConfigurationError

_ENV_PREFIX = "AURA_"


def _coerce_scalars(value: Any) -> Any:
    """Best-effort scalar coercion for environment-provided values."""
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"true", "false"}:
            return lowered == "true"
        if lowered in {"none", "null"}:
            return None
        try:
            return int(value)
        except ValueError:
            pass
        try:
            return float(value)
        except ValueError:
            pass
        return value
    if isinstance(value, dict):
        return {k: _coerce_scalars(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_coerce_scalars(v) for v in value]
    return value


def _apply_env(config: dict[str, Any], env: Mapping[str, str] | None = None) -> dict[str, Any]:
    source = env if env is not None else os.environ
    for key, raw in source.items():
        if not key.startswith(_ENV_PREFIX):
            continue
        direct = key[len(_ENV_PREFIX) :].lower()
        # exact match wins for top-level scalar fields (AURA_INSTANCE_ID -> instance_id)
        if direct in config and not isinstance(config[direct], dict):
            config[direct] = raw
            continue
        segments = direct.split("_")
        top = segments[0]
        rest = "_".join(segments[1:])
        if not rest:
            config[top] = raw
            continue
        section = config.get(top)
        if not isinstance(section, dict):
            section = {}
            config[top] = section
        section[rest] = raw
    return config


class ConfigLoader:
    """Loads and validates AURA configuration from layered sources."""

    def load(
        self,
        *,
        config_path: str | Path | None = None,
        env: Mapping[str, str] | None = None,
        overrides: dict[str, Any] | None = None,
    ) -> AuraConfig:
        raw: dict[str, Any] = AuraConfig().model_dump()
        path = Path(config_path) if config_path else None
        if path is None and os.environ.get("AURA_CONFIG"):
            path = Path(os.environ["AURA_CONFIG"])
        if path is not None:
            raw.update(_apply_env(self._read_file(path), env={}))
        raw = _apply_env(raw, env=env)
        if overrides:
            raw.update(_coerce_scalars(overrides))
        try:
            return AuraConfig.model_validate(raw)
        except Exception as exc:  # pydantic ValidationError
            raise ConfigurationError(f"invalid configuration: {exc}") from exc

    @staticmethod
    def _read_file(path: Path) -> dict[str, Any]:
        if not path.exists():
            raise ConfigurationError(f"config file not found: {path}")
        text = path.read_text(encoding="utf-8")
        if path.suffix in {".yaml", ".yml"}:
            data = yaml.safe_load(text)
        elif path.suffix == ".json":
            data = json.loads(text)
        else:
            raise ConfigurationError(f"unsupported config file extension: {path.suffix}")
        if not isinstance(data, dict):
            raise ConfigurationError(f"config file root must be a mapping: {path}")
        return cast(dict[str, Any], _coerce_scalars(data))


def validate_environment(value: str) -> Environments:
    try:
        return Environments(value)
    except ValueError as exc:
        raise ConfigurationError(f"unknown AURA environment: {value!r}") from exc


def load_settings(
    *,
    environment: str = "development",
    config_path: str | Path | None = None,
    overrides: dict[str, Any] | None = None,
) -> AuraConfig:
    """Convenience loader producing validated settings.

    Defaults are merged from a development-safe base, then environment,
    file, and overrides are applied before a single validation pass — so a
    production config is validated as a whole (never rejected mid-build).
    """
    validate_environment(environment)
    raw: dict[str, Any] = AuraConfig().model_dump()
    raw["environment"] = _coerce_scalars(environment)
    if config_path:
        raw.update(ConfigLoader._read_file(Path(config_path)))
    if overrides:
        raw.update(_coerce_scalars(overrides))
    try:
        return AuraConfig.model_validate(raw)
    except Exception as exc:  # pydantic ValidationError
        raise ConfigurationError(f"invalid configuration: {exc}") from exc


__all__ = ["ConfigLoader", "load_settings", "validate_environment"]