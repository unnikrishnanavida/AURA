"""Configuration profiles for aura-cli.

Profiles are plain JSON files (no extra dependency). ``load_profile`` returns
a validated settings object; invalid profiles raise :class:`ConfigInvalidError`
with a structured message.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from aura_cli.core.result import ConfigInvalidError

DEFAULT_PROFILE: dict[str, Any] = {
    "name": "default",
    "runtime": "canonical",
    "non_interactive": False,
    "output": "text",
    "timeout_seconds": 30,
    "confirmation_required": True,
}


@dataclass(frozen=True)
class CliProfile:
    """Validated CLI settings."""

    name: str
    runtime: str
    non_interactive: bool
    output: str
    timeout_seconds: float
    confirmation_required: bool
    extra: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CliProfile:
        name = data.get("name", "default")
        runtime = data.get("runtime", "canonical")
        non_interactive = bool(data.get("non_interactive", False))
        output = data.get("output", "text")
        try:
            timeout = float(data.get("timeout_seconds", 30))
        except (TypeError, ValueError) as exc:
            raise ConfigInvalidError(f"timeout_seconds must be a number: {exc}") from exc
        if output not in ("text", "json"):
            raise ConfigInvalidError(f"output must be 'text' or 'json', got {output!r}")
        if timeout <= 0:
            raise ConfigInvalidError("timeout_seconds must be positive")
        return cls(
            name=str(name),
            runtime=str(runtime),
            non_interactive=non_interactive,
            output=output,
            timeout_seconds=timeout,
            confirmation_required=bool(data.get("confirmation_required", True)),
            extra={k: v for k, v in data.items() if k not in DEFAULT_PROFILE},
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "runtime": self.runtime,
            "non_interactive": self.non_interactive,
            "output": self.output,
            "timeout_seconds": self.timeout_seconds,
            "confirmation_required": self.confirmation_required,
        }


class ProfileLoader:
    """Loads and validates CLI configuration profiles."""

    def __init__(self, search_paths: tuple[Path, ...] | None = None) -> None:
        self.search_paths = search_paths or (
            Path(".aura").resolve(),
            Path.home() / ".config" / "aura",
        )

    def load(self, name: str = "default") -> CliProfile:
        if name == "default":
            return CliProfile.from_dict(dict(DEFAULT_PROFILE))
        for base in self.search_paths:
            candidate = base / "profiles" / f"{name}.json"
            if candidate.exists():
                try:
                    data = json.loads(candidate.read_text(encoding="utf-8"))
                except (json.JSONDecodeError, OSError) as exc:
                    raise ConfigInvalidError(f"profile {name!r} is not valid JSON: {exc}") from exc
                return CliProfile.from_dict(data)
        raise ConfigInvalidError(f"profile {name!r} not found in {[str(p) for p in self.search_paths]}")

    def list_profiles(self) -> list[str]:
        found: list[str] = ["default"]
        for base in self.search_paths:
            profiles_dir = base / "profiles"
            if profiles_dir.is_dir():
                found.extend(p.stem for p in profiles_dir.glob("*.json"))
        return sorted(dict.fromkeys(found))


__all__ = ["DEFAULT_PROFILE", "CliProfile", "ProfileLoader"]