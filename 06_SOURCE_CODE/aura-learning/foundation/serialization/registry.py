"""
AURA Foundation - Serialization Registry.

Provides registration, lookup, discovery, and lifecycle management
for serialization codecs.

The registry is intentionally independent from individual codec
implementations so codec modules can be imported without creating
circular dependencies.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator
from threading import RLock
from typing import Any

try:
    from .exceptions import (
        SerializerAlreadyRegisteredError,
        SerializerNotFoundError,
    )
except ImportError:
    class SerializerAlreadyRegisteredError(Exception):
        pass

    class SerializerNotFoundError(Exception):
        pass


class SerializerRegistry:
    """Thread-safe registry for serializer/deserializer codecs."""

    def __init__(self) -> None:
        self._serializers: dict[str, Any] = {}
        self._aliases: dict[str, str] = {}
        self._defaults: dict[str, str] = {}
        self._lock = RLock()

    @staticmethod
    def _normalize(name: Any) -> str:
        value = str(name).strip().lower()

        if not value:
            raise ValueError("serializer name cannot be empty")

        return value

    def register(
        self,
        serializer: Any,
        *,
        name: str | None = None,
        aliases: Iterable[str] = (),
        replace: bool = False,
    ) -> Any:
        """Register a codec instance or codec class."""
        if serializer is None:
            raise ValueError("serializer cannot be None")

        resolved_name = name

        if resolved_name is None:
            resolved_name = getattr(serializer, "name", None)

        if resolved_name is None:
            resolved_name = getattr(serializer, "format", None)

        if resolved_name is None:
            raise ValueError(
                "serializer must expose 'name' or 'format'"
            )

        canonical = self._normalize(resolved_name)

        alias_names = {
            self._normalize(alias)
            for alias in aliases
        }

        with self._lock:
            if canonical in self._serializers and not replace:
                raise SerializerAlreadyRegisteredError(
                    f"Serializer '{canonical}' is already registered."
                )

            for alias in alias_names:
                if alias == canonical:
                    continue

                existing = self._aliases.get(alias)

                if existing is not None and existing != canonical:
                    if not replace:
                        raise SerializerAlreadyRegisteredError(
                            f"Serializer alias '{alias}' is already registered."
                        )

            self._serializers[canonical] = serializer

            for alias in alias_names:
                if alias != canonical:
                    self._aliases[alias] = canonical

        return serializer

    def register_many(
        self,
        serializers: Iterable[Any],
        *,
        replace: bool = False,
    ) -> list[Any]:
        registered = []

        for serializer in serializers:
            registered.append(
                self.register(
                    serializer,
                    replace=replace,
                )
            )

        return registered

    def unregister(
        self,
        name: str,
    ) -> Any | None:
        canonical = self.resolve_name(name)

        with self._lock:
            serializer = self._serializers.pop(
                canonical,
                None,
            )

            aliases = [
                alias
                for alias, target in self._aliases.items()
                if target == canonical
            ]

            for alias in aliases:
                self._aliases.pop(alias, None)

            return serializer

    def get(
        self,
        name: str,
        default: Any = None,
    ) -> Any:
        try:
            canonical = self.resolve_name(name)
        except (KeyError, ValueError):
            return default

        with self._lock:
            return self._serializers.get(
                canonical,
                default,
            )

    def require(
        self,
        name: str,
    ) -> Any:
        serializer = self.get(name)

        if serializer is None:
            raise SerializerNotFoundError(
                f"No serializer registered for '{name}'."
            )

        return serializer

    def contains(
        self,
        name: str,
    ) -> bool:
        return self.get(name) is not None

    def resolve_name(
        self,
        name: str,
    ) -> str:
        normalized = self._normalize(name)

        with self._lock:
            if normalized in self._serializers:
                return normalized

            canonical = self._aliases.get(normalized)

            if canonical is not None:
                return canonical

        raise KeyError(
            f"Unknown serializer '{name}'."
        )

    def aliases(
        self,
        name: str,
    ) -> list[str]:
        canonical = self.resolve_name(name)

        with self._lock:
            return [
                alias
                for alias, target in self._aliases.items()
                if target == canonical
            ]

    def names(self) -> list[str]:
        with self._lock:
            return list(self._serializers.keys())

    def serializers(self) -> list[str]:
        return self.names()

    def values(self) -> list[Any]:
        with self._lock:
            return list(self._serializers.values())

    def items(self) -> list[tuple[str, Any]]:
        with self._lock:
            return list(self._serializers.items())

    def __iter__(self) -> Iterator[str]:
        return iter(self.names())

    def __len__(self) -> int:
        with self._lock:
            return len(self._serializers)

    def __contains__(self, name: object) -> bool:
        try:
            return self.contains(str(name))
        except (TypeError, ValueError):
            return False

    def clear(self) -> None:
        with self._lock:
            self._serializers.clear()
            self._aliases.clear()

    def copy(self) -> "SerializerRegistry":
        clone = SerializerRegistry()

        with self._lock:
            clone._serializers.update(
                self._serializers
            )
            clone._aliases.update(
                self._aliases
            )

        return clone

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            return {
                "serializers": list(
                    self._serializers.keys()
                ),
                "aliases": dict(self._aliases),
            }

    def capabilities(
        self,
        name: str,
    ) -> set[str]:
        serializer = self.require(name)
        provider = getattr(
            serializer,
            "capabilities",
            None,
        )

        if callable(provider):
            return set(provider())

        capabilities: set[str] = set()

        if callable(
            getattr(serializer, "serialize", None)
        ):
            capabilities.add("serialize")

        if callable(
            getattr(serializer, "deserialize", None)
        ):
            capabilities.add("deserialize")

        if callable(
            getattr(serializer, "serialize_to_stream", None)
        ):
            capabilities.add("stream")

        if callable(
            getattr(serializer, "serialize_async", None)
        ):
            capabilities.add("async")

        return capabilities

    def find_by_extension(
        self,
        extension: str,
    ) -> Any | None:
        normalized = str(extension).strip().lower()

        if not normalized.startswith("."):
            normalized = "." + normalized

        with self._lock:
            serializers = list(
                self._serializers.values()
            )

        for serializer in serializers:
            extensions = getattr(
                serializer,
                "supported_extensions",
                None,
            )

            if callable(extensions):
                supported = {
                    str(item).lower()
                    for item in extensions()
                }

                if normalized in supported:
                    return serializer

            single = getattr(
                serializer,
                "file_extension",
                None,
            )

            if callable(single):
                if (
                    str(single()).lower()
                    == normalized
                ):
                    return serializer

        return None

    def find_for_value(
        self,
        value: Any,
    ) -> list[Any]:
        matches = []

        with self._lock:
            serializers = list(
                self._serializers.values()
            )

        for serializer in serializers:
            supports = getattr(
                serializer,
                "supports",
                None,
            )

            if callable(supports):
                try:
                    if supports(type(value)):
                        matches.append(serializer)
                        continue
                except Exception:
                    pass

                try:
                    if supports(value):
                        matches.append(serializer)
                except Exception:
                    pass

        return matches

    def health(self) -> bool:
        with self._lock:
            serializers = list(
                self._serializers.values()
            )

        for serializer in serializers:
            check = getattr(
                serializer,
                "health",
                None,
            )

            if callable(check):
                try:
                    if not bool(check()):
                        return False
                except Exception:
                    return False

        return True

    def initialize(self) -> None:
        with self._lock:
            serializers = list(
                self._serializers.values()
            )

        for serializer in serializers:
            initialize = getattr(
                serializer,
                "initialize",
                None,
            )

            if callable(initialize):
                initialize()

    def shutdown(self) -> None:
        with self._lock:
            serializers = list(
                self._serializers.values()
            )

        for serializer in serializers:
            shutdown = getattr(
                serializer,
                "shutdown",
                None,
            )

            if callable(shutdown):
                shutdown()

    def reset(self) -> None:
        with self._lock:
            serializers = list(
                self._serializers.values()
            )

        for serializer in serializers:
            reset = getattr(
                serializer,
                "reset",
                None,
            )

            if callable(reset):
                reset()

    def register_defaults(
        self,
        *,
        replace: bool = False,
    ) -> list[Any]:
        """Load the built-in codecs that are available."""
        module_names = (
            ("json", "JsonCodec"),
            ("yaml", "YamlCodec"),
            ("xml", "XmlCodec"),
            ("pickle", "PickleCodec"),
            ("msgpack", "MsgPackCodec"),
            ("toml", "TomlCodec"),
            ("csv", "CsvCodec"),
            ("ini", "IniCodec"),
            ("properties", "PropertiesCodec"),
            ("dotenv", "DotenvCodec"),
        )

        registered = []

        for module_name, class_name in module_names:
            try:
                module = __import__(
                    f"{__package__}.{module_name}",
                    fromlist=[class_name],
                )
                codec_class = getattr(
                    module,
                    class_name,
                )
                codec = codec_class()

                try:
                    registered.append(
                        self.register(
                            codec,
                            replace=replace,
                        )
                    )
                except SerializerAlreadyRegisteredError:
                    if replace:
                        raise

            except (ImportError, AttributeError):
                continue

        return registered


    # ------------------------------------------------------------------
    # Advanced metadata and discovery
    # ------------------------------------------------------------------

    def set_priority(self, name: str, priority: int) -> None:
        """Update the selection priority of a registered serializer."""
        canonical = self.resolve_name(name)
        with self._lock:
            serializer = self._serializers.get(canonical)
            if serializer is None:
                raise SerializerNotFoundError(
                    f"No serializer registered for '{name}'."
                )
            try:
                setattr(serializer, "priority", int(priority))
            except Exception:
                pass

    def priority(self, name: str) -> int:
        """Return the declared priority of a serializer."""
        serializer = self.require(name)
        value = getattr(serializer, "priority", 0)
        try:
            return int(value)
        except (TypeError, ValueError):
            return 0

    def ranked_names(self) -> list[str]:
        """Return registered serializers ordered by priority."""
        return sorted(
            self.names(),
            key=lambda item: (-self.priority(item), item),
        )

    def ranked_items(self) -> list[tuple[str, Any]]:
        """Return serializer items ordered by priority."""
        return [
            (name, self.require(name))
            for name in self.ranked_names()
        ]

    def highest_priority(self) -> Any | None:
        """Return the highest-priority registered serializer."""
        names = self.ranked_names()
        if not names:
            return None
        return self.require(names[0])

    def lowest_priority(self) -> Any | None:
        """Return the lowest-priority registered serializer."""
        names = self.ranked_names()
        if not names:
            return None
        return self.require(names[-1])

    def find_by_media_type(self, media_type: str) -> Any | None:
        """Find a serializer using a MIME/media type declaration."""
        target = str(media_type).strip().lower()
        for name in self.names():
            serializer = self.get(name)
            if serializer is None:
                continue
            declared = getattr(serializer, "media_types", None)
            if callable(declared):
                try:
                    declared = declared()
                except Exception:
                    declared = ()
            if declared and target in {
                str(item).strip().lower() for item in declared
            }:
                return serializer
            mime_types = getattr(serializer, "mime_types", None)
            if mime_types and target in {
                str(item).strip().lower() for item in mime_types
            }:
                return serializer
        return None

    def find_all_by_extension(self, extension: str) -> list[Any]:
        """Return every serializer matching a file extension."""
        target = str(extension).strip().lower()
        if target and not target.startswith("."):
            target = "." + target

        matches: list[Any] = []
        for name in self.names():
            serializer = self.get(name)
            if serializer is None:
                continue

            provider = getattr(
                serializer,
                "supported_extensions",
                None,
            )
            if callable(provider):
                try:
                    values = provider()
                except Exception:
                    values = ()
            else:
                values = getattr(
                    serializer,
                    "extensions",
                    (),
                )

            normalized = {
                str(value).strip().lower()
                for value in values or ()
            }

            single = getattr(
                serializer,
                "file_extension",
                None,
            )
            if callable(single):
                try:
                    normalized.add(
                        str(single()).strip().lower()
                    )
                except Exception:
                    pass

            if target in normalized:
                matches.append(serializer)

        matches.sort(
            key=lambda item: (
                -self.priority(
                    getattr(item, "name", "")
                ),
                str(getattr(item, "name", "")),
            )
        )
        return matches

    def find_by_tag(self, tag: str) -> list[Any]:
        """Find serializers advertising a tag."""
        wanted = str(tag).strip().lower()
        matches = []

        for name in self.names():
            serializer = self.get(name)
            if serializer is None:
                continue

            values = getattr(serializer, "tags", ())
            if callable(values):
                try:
                    values = values()
                except Exception:
                    values = ()

            if wanted in {
                str(value).strip().lower()
                for value in values or ()
            }:
                matches.append(serializer)

        return matches

    def find_by_capability(self, capability: str) -> list[Any]:
        """Find serializers exposing a named capability."""
        wanted = str(capability).strip()
        return [
            self.require(name)
            for name in self.names()
            if wanted in self.capabilities(name)
        ]

    def find_by_name_pattern(self, pattern: str) -> list[Any]:
        """Find serializers whose canonical name contains a pattern."""
        wanted = str(pattern).strip().lower()
        return [
            self.require(name)
            for name in self.names()
            if wanted in name.lower()
        ]

    def find(
        self,
        *,
        name: str | None = None,
        extension: str | None = None,
        media_type: str | None = None,
        value: Any = None,
        capability: str | None = None,
        tag: str | None = None,
    ) -> list[Any]:
        """Perform a combined serializer discovery query."""
        if name is not None:
            serializer = self.get(name)
            return [] if serializer is None else [serializer]

        if extension is not None:
            return self.find_all_by_extension(extension)

        if media_type is not None:
            serializer = self.find_by_media_type(media_type)
            return [] if serializer is None else [serializer]

        if value is not None:
            return self.find_for_value(value)

        if capability is not None:
            return self.find_by_capability(capability)

        if tag is not None:
            return self.find_by_tag(tag)

        return self.values()

    # ------------------------------------------------------------------
    # Registration inspection
    # ------------------------------------------------------------------

    def is_registered(self, name: str) -> bool:
        """Return whether a canonical name or alias is registered."""
        return self.contains(name)

    def is_alias(self, name: str) -> bool:
        """Return whether a name is currently an alias."""
        normalized = self._normalize(name)
        with self._lock:
            return normalized in self._aliases

    def canonical_name(self, name: str) -> str:
        """Return the canonical name behind an alias."""
        return self.resolve_name(name)

    def alias_map(self) -> dict[str, str]:
        """Return a copy of the alias mapping."""
        with self._lock:
            return dict(self._aliases)

    def registration_map(self) -> dict[str, Any]:
        """Return a copy of the canonical registration map."""
        with self._lock:
            return dict(self._serializers)

    def registration_count(self) -> int:
        """Return the number of canonical serializers."""
        return len(self)

    def alias_count(self) -> int:
        """Return the number of aliases."""
        with self._lock:
            return len(self._aliases)

    def empty(self) -> bool:
        """Return whether the registry has no serializers."""
        with self._lock:
            return not bool(self._serializers)

    # ------------------------------------------------------------------
    # Safe registration helpers
    # ------------------------------------------------------------------

    def ensure_registered(
        self,
        serializer: Any,
        *,
        name: str | None = None,
        aliases: Iterable[str] = (),
    ) -> Any:
        """Register a serializer only when it is not already present."""
        resolved = (
            name
            or getattr(serializer, "name", None)
            or getattr(serializer, "format", None)
        )
        if resolved is None:
            raise ValueError(
                "serializer must expose 'name' or 'format'"
            )

        if self.contains(resolved):
            return self.require(resolved)

        return self.register(
            serializer,
            name=name,
            aliases=aliases,
        )

    def replace(
        self,
        serializer: Any,
        *,
        name: str | None = None,
        aliases: Iterable[str] = (),
    ) -> Any:
        """Replace an existing serializer registration."""
        return self.register(
            serializer,
            name=name,
            aliases=aliases,
            replace=True,
        )

    def register_aliases(
        self,
        name: str,
        aliases: Iterable[str],
        *,
        replace: bool = False,
    ) -> list[str]:
        """Register multiple aliases for one serializer."""
        added = []
        for alias in aliases:
            self.add_alias(
                name,
                alias,
                replace=replace,
            )
            added.append(
                self._normalize(alias)
            )
        return added

    def remove_aliases(self, name: str) -> list[str]:
        """Remove all aliases belonging to a serializer."""
        canonical = self.resolve_name(name)
        aliases = self.aliases(canonical)
        for alias in aliases:
            self.remove_alias(alias)
        return aliases

    def unregister_many(
        self,
        names: Iterable[str],
    ) -> list[Any]:
        """Remove several serializers and return removed codecs."""
        removed = []
        for name in names:
            serializer = self.unregister(name)
            if serializer is not None:
                removed.append(serializer)
        return removed

    # ------------------------------------------------------------------
    # Default selection
    # ------------------------------------------------------------------

    def set_default_serializer(
        self,
        name: str,
        *,
        purpose: str = "general",
    ) -> None:
        """Set a serializer as the default for a purpose."""
        canonical = self.resolve_name(name)
        with self._lock:
            setattr(
                self,
                "_defaults",
                getattr(self, "_defaults", {}),
            )
            self._defaults[
                str(purpose).strip().lower()
            ] = canonical

    def default_serializer(
        self,
        purpose: str = "general",
    ) -> Any | None:
        """Return the configured default serializer."""
        defaults = getattr(
            self,
            "_defaults",
            {},
        )
        name = defaults.get(
            str(purpose).strip().lower()
        )
        if name is None:
            return None
        return self.get(name)

    def default_serializer_name(
        self,
        purpose: str = "general",
    ) -> str | None:
        """Return the canonical name of a configured default."""
        defaults = getattr(
            self,
            "_defaults",
            {},
        )
        return defaults.get(
            str(purpose).strip().lower()
        )

    def clear_default(
        self,
        purpose: str = "general",
    ) -> None:
        """Remove a configured default serializer."""
        defaults = getattr(
            self,
            "_defaults",
            {},
        )
        defaults.pop(
            str(purpose).strip().lower(),
            None,
        )

    # ------------------------------------------------------------------
    # Capability predicates
    # ------------------------------------------------------------------

    def can_serialize(self, name: str) -> bool:
        """Return whether a codec exposes serialization."""
        return "serialize" in self.capabilities(name)

    def can_deserialize(self, name: str) -> bool:
        """Return whether a codec exposes deserialization."""
        return "deserialize" in self.capabilities(name)

    def can_stream(self, name: str) -> bool:
        """Return whether a codec supports stream operations."""
        values = self.capabilities(name)
        return (
            "stream" in values
            or "serialize_to_stream" in values
            or "deserialize_from_stream" in values
        )

    def can_async(self, name: str) -> bool:
        """Return whether a codec exposes asynchronous operations."""
        values = self.capabilities(name)
        return (
            "async" in values
            or "serialize_async" in values
            or "deserialize_async" in values
        )

    def is_bidirectional(self, name: str) -> bool:
        """Return whether a codec can both encode and decode."""
        return (
            self.can_serialize(name)
            and self.can_deserialize(name)
        )

    def bidirectional(self) -> list[Any]:
        """Return all codecs supporting both directions."""
        return [
            self.require(name)
            for name in self.names()
            if self.is_bidirectional(name)
        ]

    # ------------------------------------------------------------------
    # Codec lifecycle helpers
    # ------------------------------------------------------------------

    def initialize_one(self, name: str) -> Any:
        """Initialize one codec if it exposes initialize()."""
        serializer = self.require(name)
        operation = getattr(
            serializer,
            "initialize",
            None,
        )
        if callable(operation):
            operation()
        return serializer

    def shutdown_one(self, name: str) -> Any:
        """Shutdown one codec if it exposes shutdown()."""
        serializer = self.require(name)
        operation = getattr(
            serializer,
            "shutdown",
            None,
        )
        if callable(operation):
            operation()
        return serializer

    def reset_one(self, name: str) -> Any:
        """Reset one codec if it exposes reset()."""
        serializer = self.require(name)
        operation = getattr(
            serializer,
            "reset",
            None,
        )
        if callable(operation):
            operation()
        return serializer

    def health_one(self, name: str) -> bool:
        """Check one codec's health."""
        serializer = self.require(name)
        operation = getattr(
            serializer,
            "health",
            None,
        )
        if not callable(operation):
            return True
        try:
            return bool(operation())
        except Exception:
            return False

    def health_report(self) -> dict[str, bool]:
        """Return per-codec health status."""
        return {
            name: self.health_one(name)
            for name in self.names()
        }

    def unhealthy(self) -> list[str]:
        """Return names of codecs failing health checks."""
        return [
            name
            for name, healthy
            in self.health_report().items()
            if not healthy
        ]

    # ------------------------------------------------------------------
    # Statistics and diagnostics
    # ------------------------------------------------------------------

    def statistics(self) -> dict[str, Any]:
        """Return useful registry statistics."""
        names = self.names()
        aliases = self.alias_map()

        capabilities: dict[str, int] = {}
        for name in names:
            for capability in self.capabilities(name):
                capabilities[capability] = (
                    capabilities.get(capability, 0) + 1
                )

        return {
            "serializers": len(names),
            "aliases": len(aliases),
            "capabilities": capabilities,
            "healthy": self.health(),
        }

    def diagnostics(self) -> dict[str, Any]:
        """Return a complete registry diagnostic snapshot."""
        return {
            "statistics": self.statistics(),
            "names": self.names(),
            "aliases": self.alias_map(),
            "health": self.health_report(),
            "defaults": getattr(
                self,
                "_defaults",
                {},
            ).copy(),
        }

    def describe(self, name: str) -> dict[str, Any]:
        """Describe one serializer using its public attributes."""
        canonical = self.resolve_name(name)
        serializer = self.require(canonical)

        capabilities = sorted(
            self.capabilities(canonical)
        )

        extensions = getattr(
            serializer,
            "supported_extensions",
            (),
        )
        if callable(extensions):
            try:
                extensions = extensions()
            except Exception:
                extensions = ()

        media_types = getattr(
            serializer,
            "media_types",
            (),
        )
        if callable(media_types):
            try:
                media_types = media_types()
            except Exception:
                media_types = ()

        return {
            "name": canonical,
            "aliases": self.aliases(canonical),
            "extensions": list(extensions or ()),
            "media_types": list(media_types or ()),
            "priority": self.priority(canonical),
            "capabilities": capabilities,
            "type": type(serializer).__name__,
            "module": type(serializer).__module__,
        }

    def describe_all(self) -> list[dict[str, Any]]:
        """Describe every registered serializer."""
        return [
            self.describe(name)
            for name in self.names()
        ]

    # ------------------------------------------------------------------
    # Snapshot and restoration helpers
    # ------------------------------------------------------------------

    def snapshot_full(self) -> dict[str, Any]:
        """Capture registrations, aliases, and defaults."""
        with self._lock:
            return {
                "serializers": dict(
                    self._serializers
                ),
                "aliases": dict(
                    self._aliases
                ),
                "defaults": dict(
                    getattr(
                        self,
                        "_defaults",
                        {},
                    )
                ),
            }

    def restore_full(
        self,
        snapshot: dict[str, Any],
    ) -> None:
        """Restore a snapshot produced by snapshot_full()."""
        if not isinstance(snapshot, dict):
            raise TypeError(
                "snapshot must be a dictionary"
            )

        serializers = snapshot.get(
            "serializers",
            {},
        )
        aliases = snapshot.get(
            "aliases",
            {},
        )
        defaults = snapshot.get(
            "defaults",
            {},
        )

        if not isinstance(serializers, dict):
            raise TypeError(
                "snapshot['serializers'] must be a dictionary"
            )

        with self._lock:
            self._serializers = dict(
                serializers
            )
            self._aliases = dict(
                aliases
            )
            self._defaults = dict(
                defaults
            )

    def restore(
        self,
        snapshot: dict[str, Any],
    ) -> None:
        """Alias for restore_full()."""
        self.restore_full(snapshot)

    # ------------------------------------------------------------------
    # Transaction-like context
    # ------------------------------------------------------------------

    @contextmanager
    def atomic(self):
        """Temporarily apply changes and restore on failure."""
        snapshot = self.snapshot_full()
        try:
            yield self
        except Exception:
            self.restore_full(snapshot)
            raise

    # ------------------------------------------------------------------
    # Dynamic loading
    # ------------------------------------------------------------------

    def load_module(
        self,
        module_name: str,
        *,
        register_function: str = "register",
    ) -> Any:
        """Import a module and optionally call its registration hook."""
        import importlib

        module = importlib.import_module(
            module_name
        )

        hook = getattr(
            module,
            register_function,
            None,
        )

        if callable(hook):
            result = hook(self)
            return (
                module
                if result is None
                else result
            )

        return module

    def load_codec_class(
        self,
        module_name: str,
        class_name: str,
        **kwargs: Any,
    ) -> Any:
        """Load, instantiate, and register a codec class."""
        import importlib

        module = importlib.import_module(
            module_name
        )

        codec_class = getattr(
            module,
            class_name,
        )

        codec = codec_class(
            **kwargs
        )

        self.register(codec)
        return codec

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def validate_name(self, name: str) -> bool:
        """Validate that a name resolves to a serializer."""
        try:
            return self.contains(name)
        except (TypeError, ValueError):
            return False

    def validate_serializer(
        self,
        serializer: Any,
    ) -> tuple[bool, list[str]]:
        """Validate the minimum codec contract."""
        errors: list[str] = []

        if serializer is None:
            return False, [
                "serializer cannot be None"
            ]

        name = getattr(
            serializer,
            "name",
            None,
        ) or getattr(
            serializer,
            "format",
            None,
        )

        if not name:
            errors.append(
                "serializer must expose name or format"
            )

        if not callable(
            getattr(
                serializer,
                "serialize",
                None,
            )
        ) and not callable(
            getattr(
                serializer,
                "deserialize",
                None,
            )
        ):
            errors.append(
                "serializer must expose serialize "
                "or deserialize"
            )

        return not errors, errors

    def assert_valid_serializer(
        self,
        serializer: Any,
    ) -> Any:
        """Raise ValueError if a codec violates the minimum contract."""
        valid, errors = self.validate_serializer(
            serializer
        )
        if not valid:
            raise ValueError(
                "; ".join(errors)
            )
        return serializer

    # ------------------------------------------------------------------
    # Compatibility and cloning
    # ------------------------------------------------------------------

    def compatible(
        self,
        first: str,
        second: str,
    ) -> bool:
        """Check whether two names resolve to the same codec."""
        try:
            return (
                self.resolve_name(first)
                == self.resolve_name(second)
            )
        except (KeyError, ValueError):
            return False

    def clone(
        self,
    ) -> "SerializerRegistry":
        """Create an independent registry with the same registrations."""
        clone = SerializerRegistry()

        with self._lock:
            clone._serializers = dict(
                self._serializers
            )
            clone._aliases = dict(
                self._aliases
            )
            clone._defaults = dict(
                getattr(
                    self,
                    "_defaults",
                    {},
                )
            )

        return clone

    # ------------------------------------------------------------------
    # Serialization selection policy
    # ------------------------------------------------------------------

    def choose_for_value(
        self,
        value: Any,
        *,
        preferred: Iterable[str] = (),
    ) -> Any:
        """Choose the best serializer for a value."""
        preferred_names = list(
            preferred
        )

        for name in preferred_names:
            serializer = self.get(name)
            if serializer is None:
                continue

            supports = getattr(
                serializer,
                "supports",
                None,
            )

            if not callable(supports):
                continue

            try:
                if supports(type(value)):
                    return serializer
            except Exception:
                pass

            try:
                if supports(value):
                    return serializer
            except Exception:
                pass

        matches = self.find_for_value(
            value
        )
        if not matches:
            raise SerializerNotFoundError(
                "No serializer supports "
                f"value type '{type(value).__name__}'."
            )

        return matches[0]

    def choose_for_filename(
        self,
        filename: str,
    ) -> Any:
        """Choose a serializer from a filename."""
        serializer = self.find_by_extension(
            filename
            if str(filename).startswith(".")
            else str(filename).split(".")[-1]
        )

        if serializer is None:
            raise SerializerNotFoundError(
                f"No serializer registered for '{filename}'."
            )

        return serializer

    def choose_for_media_type(
        self,
        media_type: str,
    ) -> Any:
        """Choose a serializer from a MIME type."""
        serializer = self.find_by_media_type(
            media_type
        )
        if serializer is None:
            raise SerializerNotFoundError(
                f"No serializer registered for '{media_type}'."
            )
        return serializer

    # ------------------------------------------------------------------
    # Mapping and export
    # ------------------------------------------------------------------

    def to_mapping(self) -> dict[str, Any]:
        """Return the canonical registry mapping."""
        with self._lock:
            return dict(
                self._serializers
            )

    def to_name_list(self) -> list[str]:
        """Return canonical names as a list."""
        return self.names()

    def to_alias_mapping(self) -> dict[str, str]:
        """Return aliases as canonical-name mappings."""
        return self.alias_map()

    def export_metadata(self) -> dict[str, dict[str, Any]]:
        """Export metadata for all registered codecs."""
        return {
            name: self.describe(name)
            for name in self.names()
        }

    # ------------------------------------------------------------------
    # Search convenience
    # ------------------------------------------------------------------

    def search(self, query: str) -> list[Any]:
        """Search names, aliases, tags, and descriptions."""
        wanted = str(query).strip().lower()
        matches = []

        for name in self.names():
            serializer = self.require(name)
            metadata = (
                getattr(
                    serializer,
                    "description",
                    "",
                )
                or ""
            )

            aliases = self.aliases(name)
            tags = getattr(
                serializer,
                "tags",
                (),
            )
            if callable(tags):
                try:
                    tags = tags()
                except Exception:
                    tags = ()

            haystack = " ".join(
                [
                    name,
                    *aliases,
                    str(metadata),
                    *map(str, tags or ()),
                ]
            ).lower()

            if wanted in haystack:
                matches.append(serializer)

        return matches

    def search_names(self, query: str) -> list[str]:
        """Search and return canonical names."""
        return [
            getattr(
                serializer,
                "name",
                self._normalize(
                    str(serializer)
                ),
            )
            for serializer in self.search(query)
        ]

    # ------------------------------------------------------------------
    # Thread-safe utility helpers
    # ------------------------------------------------------------------

    @contextmanager
    def locked(self):
        """Expose the registry lock for compound external operations."""
        with self._lock:
            yield self

    def update(
        self,
        serializers: Mapping[str, Any],
        *,
        replace: bool = False,
    ) -> list[Any]:
        """Register a mapping of canonical names to codecs."""
        registered = []

        for name, serializer in serializers.items():
            registered.append(
                self.register(
                    serializer,
                    name=name,
                    replace=replace,
                )
            )

        return registered

    def pop(
        self,
        name: str,
        default: Any = None,
    ) -> Any:
        """Dictionary-style removal helper."""
        serializer = self.unregister(name)
        if serializer is None:
            return default
        return serializer

    def get_or_default(
        self,
        name: str,
        *,
        purpose: str = "general",
    ) -> Any:
        """Return a named serializer or the configured default."""
        serializer = self.get(name)
        if serializer is not None:
            return serializer

        default = self.default_serializer(
            purpose
        )
        if default is None:
            raise SerializerNotFoundError(
                f"No serializer '{name}' and no default "
                f"configured for '{purpose}'."
            )

        return default

    # ------------------------------------------------------------------
    # Final cleanup and context management
    # ------------------------------------------------------------------

    def clear_aliases(self) -> None:
        """Remove every alias while retaining canonical serializers."""
        with self._lock:
            self._aliases.clear()

    def close(self) -> None:
        """Close all serializers and clear registry state."""
        self.shutdown()
        self.clear()

    def __enter__(self) -> "SerializerRegistry":
        self._lock.acquire()
        return self

    def __exit__(
        self,
        exc_type: Any,
        exc_value: Any,
        traceback: Any,
    ) -> bool:
        self._lock.release()
        return False

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"serializers={len(self)}, "
            f"aliases={self.alias_count()})"
        )

    def __bool__(self) -> bool:
        return not self.empty()


serializer_registry = SerializerRegistry()


__all__ = [
    "SerializerRegistry",
    "serializer_registry",
]