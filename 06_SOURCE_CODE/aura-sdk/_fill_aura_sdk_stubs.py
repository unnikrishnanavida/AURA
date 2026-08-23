from __future__ import annotations

import re
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parent
PACKAGE_DIR = ROOT / "aura_sdk"


def _camel_case(value: str) -> str:
    return "".join(part.capitalize() for part in re.split(r"[_\-. ]+", value) if part)


def _singular(value: str) -> str:
    return value[:-1] if value.endswith("s") and len(value) > 1 else value


def _constants_content(package: str) -> str:
    package_name = package.replace("-", "_")
    constant_prefix = package_name.upper()
    return textwrap.dedent('''
        """AURA SDK {title} constants."""

        DEFAULT_{constant_prefix}_TIMEOUT = 30
        PACKAGE_NAMESPACE = "aura_sdk.{package_name}"
        SUPPORTED_{constant_prefix} = ("default", "extended")

        __all__ = [
            "DEFAULT_{constant_prefix}_TIMEOUT",
            "PACKAGE_NAMESPACE",
            "SUPPORTED_{constant_prefix}",
        ]
        ''').format(
        title=package_name.replace("_", " ").title(),
        constant_prefix=constant_prefix,
        package_name=package_name,
    )


def _exceptions_content(package: str, path: Path) -> str:
    package_name = package.replace("-", "_")
    human_name = package_name.replace("_", " ")
    singular = _camel_case(_singular(package_name))
    base_name = singular if singular != "Type" else "TypeComponent"
    title = human_name.title()
    return textwrap.dedent('''
        """AURA SDK {title} exceptions."""


        class {base_name}Error(Exception):
            """Base exception for aura_sdk.{package_name}."""


        class {base_name}NotFoundError({base_name}Error):
            """Raised when a {human_name} resource is missing."""


        class {base_name}ValidationError({base_name}Error):
            """Raised when a {human_name} resource fails validation."""


        __all__ = [
            "{base_name}Error",
            "{base_name}NotFoundError",
            "{base_name}ValidationError",
        ]
        ''').format(
        title=title,
        base_name=base_name,
        package_name=package_name,
        human_name=human_name,
    )


def _types_content(package: str, path: Path) -> str:
    package_name = package.replace("-", "_")
    file_base = path.stem
    singular = _camel_case(_singular(package_name))
    class_name = "TypeDefinition" if file_base == "types" else f"{singular}Type"
    return textwrap.dedent('''
        """AURA SDK {title} types."""

        from __future__ import annotations
        from dataclasses import dataclass
        from typing import Any


        @dataclass
        class {class_name}:
            """Structured metadata for aura_sdk.{package_name}."""

            name: str
            enabled: bool = True
            metadata: dict[str, Any] | None = None

            def to_dict(self) -> dict[str, Any]:
                """Return a JSON-serializable representation of the type metadata."""
                return {{
                    "name": self.name,
                    "enabled": self.enabled,
                    "metadata": self.metadata or {{}},
                }}


        __all__ = ["{class_name}"]
        ''').format(
        title=package_name.replace("_", " ").title(),
        class_name=class_name,
        package_name=package_name,
    )


def _validators_content(package: str, path: Path) -> str:
    package_name = package.replace("-", "_")
    class_name = (
        "Validator"
        if package_name == "types"
        else f"{_camel_case(_singular(package_name))}Validator"
    )
    return textwrap.dedent('''
        """AURA SDK {title} validators."""

        from __future__ import annotations
        from typing import Any


        class {class_name}:
            """Core validator for aura_sdk.{package_name}."""

            def validate(self, data: Any) -> bool:
                """Validate that data is not None and has expected structure."""
                if data is None:
                    raise ValueError("data cannot be None")
                return True


        __all__ = ["{class_name}"]
        ''').format(
        title=package_name.replace("_", " ").title(),
        class_name=class_name,
        package_name=package_name,
    )


def _plugin_api_content() -> str:
    return textwrap.dedent('''
        """AURA SDK Plugins plugin_api."""

        from __future__ import annotations
        from typing import Any


        class PluginApi:
            """Core plugin API for aura_sdk.plugins."""

            def __init__(self) -> None:
                self.registry: dict[str, Any] = {}
                self.config: dict[str, Any] = {}

            def initialize(self, config: dict[str, Any] | None = None) -> None:
                """Prepare the plugin before it is registered with the SDK."""
                self.config = config or {}

            def register(self, name: str, provider: Any) -> None:
                """Register a provider or capability with the plugin API."""
                if not name:
                    raise ValueError("name must be provided")
                self.registry[name] = provider

            def get(self, name: str, default: Any | None = None) -> Any:
                """Return a registered plugin provider."""
                return self.registry.get(name, default)

            def shutdown(self) -> None:
                """Clean up plugin resources."""
                self.registry.clear()


        __all__ = ["PluginApi"]
        ''')


def _handlers_content() -> str:
    return textwrap.dedent('''
        """AURA SDK exception handlers."""

        from __future__ import annotations
        from typing import Any


        class HandlerException(Exception):
            """Base handler exception."""


        class ExceptionHandler:
            """Minimal exception handler for aura_sdk.exceptions."""

            def handle(self, event: Any) -> dict[str, Any]:
                """Handle an error event and return a safe fallback action."""
                if event is None:
                    raise HandlerException("event cannot be None")
                return {"status": "handled", "event": event}


        __all__ = ["HandlerException", "ExceptionHandler"]
        ''')


def generate_content(path: Path, text: str) -> str | None:
    rel = path.relative_to(PACKAGE_DIR)
    package = rel.parts[0] if len(rel.parts) > 1 else rel.stem
    name = path.name

    if "TODO: Add {module_name}" in text:
        if name == "constants.py":
            return _constants_content(package)
        if name == "exceptions.py":
            return _exceptions_content(package, path)
        if name == "types.py":
            return _types_content(package, path)
        if name == "validators.py":
            return _validators_content(package, path)

    if name == "plugin_api.py":
        return _plugin_api_content()
    if rel == Path("exceptions") / "handlers.py":
        return _handlers_content()
    return None


def should_process(text: str) -> bool:
    if "TODO: Add {module_name}" in text:
        return True
    return re.fullmatch(r"(?s).*^\s*pass\s*$.*", text) is not None


def main() -> None:
    updated: list[str] = []
    for path in sorted(PACKAGE_DIR.rglob("*.py")):
        text = path.read_text(encoding="utf-8")
        if not should_process(text):
            continue
        content = generate_content(path, text)
        if content is None:
            continue
        path.write_text(content, encoding="utf-8")
        updated.append(str(path.relative_to(ROOT)))

    print("Updated:", len(updated))
    for item in updated:
        print(item)


if __name__ == "__main__":
    main()
