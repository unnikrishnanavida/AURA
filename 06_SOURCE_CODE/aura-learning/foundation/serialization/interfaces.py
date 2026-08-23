"""
==============================================================
AURA Framework

Foundation Serialization Interfaces
Enterprise Serialization Contracts

This module defines the abstract contracts shared by the AURA
serialization stack.

The interfaces intentionally describe behavior rather than concrete
format implementations. JSON, YAML, CSV, TOML, XML, Pickle, MsgPack,
INI, Properties, and Dotenv codecs can therefore implement the same
contracts while retaining format-specific behavior.

The contracts cover:
- serializer / deserializer operations
- combined codec operations
- file and stream support
- asynchronous operations
- request/response processing
- schema and validation
- compression and encryption hooks
- pipelines
- registry management
- configuration
- lifecycle
- statistics, metrics and health
- discovery and capabilities
- diagnostics
- runtime information
- export/import
- cloning, reset and disposal
==============================================================
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import (
    Any,
    BinaryIO,
    Callable,
    IO,
    Iterable,
    Mapping,
    Sequence,
    TextIO,
    TypeVar,
)


SerializedData = str | bytes
FormatName = str
SerializerName = str
SerializationContext = Mapping[str, Any]
InputStream = IO[Any]
OutputStream = IO[Any]

T = TypeVar("T")


# ==============================================================
# Core Serializer
# ==============================================================

class BaseSerializer(ABC):
    """Minimum contract for an AURA serializer."""

    @property
    @abstractmethod
    def name(self) -> SerializerName:
        """Canonical serializer name."""

    @property
    def format(self) -> FormatName:
        """Format identifier; defaults to the canonical name."""
        return self.name

    @abstractmethod
    def serialize(
        self,
        value: Any,
        *,
        context: SerializationContext | None = None,
    ) -> SerializedData:
        """Serialize a Python value."""

    def serialize_request(
        self,
        request: Any,
    ) -> Any:
        """Serialize a standard serialization request."""
        return self.serialize(
            request.value,
            context=getattr(
                request,
                "context",
                None,
            ),
        )

    def serialize_many(
        self,
        values: Iterable[Any],
        *,
        context: SerializationContext | None = None,
    ) -> list[SerializedData]:
        """Serialize multiple values using the same codec."""
        return [
            self.serialize(
                value,
                context=context,
            )
            for value in values
        ]

    def validate(
        self,
        value: Any,
    ) -> bool:
        """Return whether the value can be serialized."""
        try:
            self.serialize(value)
            return True
        except Exception:
            return False


# ==============================================================
# Core Deserializer
# ==============================================================

class BaseDeserializer(ABC):
    """Minimum contract for an AURA deserializer."""

    @property
    @abstractmethod
    def name(self) -> SerializerName:
        """Canonical serializer/deserializer name."""

    @property
    def format(self) -> FormatName:
        """Format identifier."""
        return self.name

    @abstractmethod
    def deserialize(
        self,
        data: SerializedData,
        *,
        context: SerializationContext | None = None,
    ) -> Any:
        """Deserialize serialized data."""

    def deserialize_request(
        self,
        request: Any,
    ) -> Any:
        """Deserialize a standard deserialization request."""
        return self.deserialize(
            request.data,
            context=getattr(
                request,
                "context",
                None,
            ),
        )

    def deserialize_many(
        self,
        values: Iterable[SerializedData],
        *,
        context: SerializationContext | None = None,
    ) -> list[Any]:
        """Deserialize multiple values."""
        return [
            self.deserialize(
                value,
                context=context,
            )
            for value in values
        ]

    def validate_data(
        self,
        data: SerializedData,
    ) -> bool:
        """Return whether serialized data can be decoded."""
        try:
            self.deserialize(data)
            return True
        except Exception:
            return False


# ==============================================================
# Combined Codec
# ==============================================================

class BaseCodec(
    BaseSerializer,
    BaseDeserializer,
):
    """Combined serializer/deserializer contract."""

    @property
    def capabilities(self) -> set[str]:
        """Return the codec's supported operations."""
        return {
            "serialize",
            "deserialize",
        }

    def supports(
        self,
        value: Any,
    ) -> bool:
        """Return whether this codec accepts the supplied value."""
        return True

    def clone(self) -> "BaseCodec":
        """Return a configured copy when cloning is supported."""
        raise NotImplementedError(
            "This codec does not implement clone()."
        )


# ==============================================================
# Stream Interfaces
# ==============================================================

class StreamSerializer(ABC):
    """Synchronous stream serializer."""

    @abstractmethod
    def serialize_to_stream(
        self,
        value: Any,
        stream: OutputStream,
        *,
        context: SerializationContext | None = None,
    ) -> None:
        """Serialize directly into an output stream."""


class StreamDeserializer(ABC):
    """Synchronous stream deserializer."""

    @abstractmethod
    def deserialize_from_stream(
        self,
        stream: InputStream,
        *,
        context: SerializationContext | None = None,
    ) -> Any:
        """Deserialize directly from an input stream."""


class FileSerializer(ABC):
    """File-oriented serializer contract."""

    @abstractmethod
    def serialize_to_file(
        self,
        value: Any,
        path: str | Path,
        *,
        context: SerializationContext | None = None,
    ) -> Path:
        """Serialize a value to a file."""


class FileDeserializer(ABC):
    """File-oriented deserializer contract."""

    @abstractmethod
    def deserialize_from_file(
        self,
        path: str | Path,
        *,
        context: SerializationContext | None = None,
    ) -> Any:
        """Deserialize a value from a file."""


class AsyncSerializer(ABC):
    """Asynchronous serializer."""

    @abstractmethod
    async def serialize(
        self,
        value: Any,
        *,
        context: SerializationContext | None = None,
    ) -> SerializedData:
        """Serialize asynchronously."""


class AsyncDeserializer(ABC):
    """Asynchronous deserializer."""

    @abstractmethod
    async def deserialize(
        self,
        data: SerializedData,
        *,
        context: SerializationContext | None = None,
    ) -> Any:
        """Deserialize asynchronously."""


class AsyncStreamSerializer(ABC):
    """Asynchronous stream serializer."""

    @abstractmethod
    async def serialize_to_stream(
        self,
        value: Any,
        stream: OutputStream,
        *,
        context: SerializationContext | None = None,
    ) -> None:
        """Serialize asynchronously to a stream."""


class AsyncStreamDeserializer(ABC):
    """Asynchronous stream deserializer."""

    @abstractmethod
    async def deserialize_from_stream(
        self,
        stream: InputStream,
        *,
        context: SerializationContext | None = None,
    ) -> Any:
        """Deserialize asynchronously from a stream."""


class AsyncFileSerializer(ABC):
    """Asynchronous file serializer."""

    @abstractmethod
    async def serialize_to_file(
        self,
        value: Any,
        path: str | Path,
        *,
        context: SerializationContext | None = None,
    ) -> Path:
        """Serialize asynchronously to a file."""


class AsyncFileDeserializer(ABC):
    """Asynchronous file deserializer."""

    @abstractmethod
    async def deserialize_from_file(
        self,
        path: str | Path,
        *,
        context: SerializationContext | None = None,
    ) -> Any:
        """Deserialize asynchronously from a file."""


# ==============================================================
# Request Processing
# ==============================================================

class RequestSerializer(ABC):
    """Request-aware serializer."""

    @abstractmethod
    def serialize_request(
        self,
        request: Any,
    ) -> Any:
        """Serialize a SerializationRequest."""


class RequestDeserializer(ABC):
    """Request-aware deserializer."""

    @abstractmethod
    def deserialize_request(
        self,
        request: Any,
    ) -> Any:
        """Deserialize a DeserializationRequest."""


class ResponseSerializer(ABC):
    """Response-aware serializer."""

    @abstractmethod
    def serialize_response(
        self,
        response: Any,
    ) -> SerializedData:
        """Serialize a serialization response."""


class ResponseDeserializer(ABC):
    """Response-aware deserializer."""

    @abstractmethod
    def deserialize_response(
        self,
        data: SerializedData,
    ) -> Any:
        """Deserialize a serialization response."""


# ==============================================================
# Schema
# ==============================================================

class BaseSchema(ABC):
    """Schema contract for serialization validation."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Schema name."""

    @abstractmethod
    def validate(
        self,
        value: Any,
    ) -> bool:
        """Validate a Python value."""

    def errors(
        self,
        value: Any,
    ) -> list[str]:
        """Return validation errors."""
        return [] if self.validate(value) else [
            f"Value does not satisfy schema '{self.name}'."
        ]

    def normalize(
        self,
        value: Any,
    ) -> Any:
        """Normalize a value according to the schema."""
        return value

    def schema(
        self,
    ) -> Mapping[str, Any]:
        """Return a serializable schema description."""
        return {
            "name": self.name,
        }


class SchemaProvider(ABC):
    """Provider for a codec's schema."""

    @abstractmethod
    def schema(
        self,
    ) -> BaseSchema | Mapping[str, Any]:
        """Return the codec schema."""


# ==============================================================
# Compression
# ==============================================================

class Compressor(ABC):
    """Compression provider."""

    @property
    @abstractmethod
    def algorithm(self) -> str:
        """Compression algorithm name."""

    @abstractmethod
    def compress(
        self,
        data: bytes,
        *,
        level: int | None = None,
    ) -> bytes:
        """Compress bytes."""

    def supports_level(
        self,
        level: int,
    ) -> bool:
        """Return whether a compression level is supported."""
        return True


class Decompressor(ABC):
    """Decompression provider."""

    @property
    @abstractmethod
    def algorithm(self) -> str:
        """Compression algorithm name."""

    @abstractmethod
    def decompress(
        self,
        data: bytes,
    ) -> bytes:
        """Decompress bytes."""


class CompressionProvider(ABC):
    """Combined compression capability."""

    @abstractmethod
    def compressor(self) -> Compressor:
        """Return a compressor."""

    @abstractmethod
    def decompressor(self) -> Decompressor:
        """Return a decompressor."""


# ==============================================================
# Encryption
# ==============================================================

class Encryptor(ABC):
    """Encryption provider."""

    @property
    @abstractmethod
    def algorithm(self) -> str:
        """Encryption algorithm."""

    @abstractmethod
    def encrypt(
        self,
        data: bytes,
        *,
        key: bytes | str,
        context: SerializationContext | None = None,
    ) -> bytes:
        """Encrypt bytes."""


class Decryptor(ABC):
    """Decryption provider."""

    @property
    @abstractmethod
    def algorithm(self) -> str:
        """Encryption algorithm."""

    @abstractmethod
    def decrypt(
        self,
        data: bytes,
        *,
        key: bytes | str,
        context: SerializationContext | None = None,
    ) -> bytes:
        """Decrypt bytes."""


class EncryptionProvider(ABC):
    """Combined encryption capability."""

    @abstractmethod
    def encryptor(self) -> Encryptor:
        """Return an encryptor."""

    @abstractmethod
    def decryptor(self) -> Decryptor:
        """Return a decryptor."""


# ==============================================================
# Pipeline
# ==============================================================

class PipelineStage(ABC):
    """One transformation stage in a serialization pipeline."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Stage name."""

    @abstractmethod
    def process(
        self,
        value: Any,
        *,
        context: SerializationContext | None = None,
    ) -> Any:
        """Process one pipeline value."""

    def reverse(
        self,
        value: Any,
        *,
        context: SerializationContext | None = None,
    ) -> Any:
        """Reverse the stage when supported."""
        return value


class Pipeline(ABC):
    """Composable serialization pipeline."""

    @abstractmethod
    def stages(self) -> Sequence[PipelineStage]:
        """Return pipeline stages."""

    @abstractmethod
    def execute(
        self,
        value: Any,
        *,
        context: SerializationContext | None = None,
    ) -> Any:
        """Execute the pipeline."""

    @abstractmethod
    def reverse(
        self,
        value: Any,
        *,
        context: SerializationContext | None = None,
    ) -> Any:
        """Reverse the pipeline."""


class Middleware(ABC):
    """Middleware hook around serialization operations."""

    @abstractmethod
    def before(
        self,
        operation: str,
        value: Any,
        *,
        context: SerializationContext | None = None,
    ) -> Any:
        """Run before an operation."""

    def after(
        self,
        operation: str,
        value: Any,
        result: Any,
        *,
        context: SerializationContext | None = None,
    ) -> Any:
        """Run after an operation."""
        return result

    def on_error(
        self,
        operation: str,
        value: Any,
        error: Exception,
        *,
        context: SerializationContext | None = None,
    ) -> None:
        """Observe an operation error."""


# ==============================================================
# Registry Management
# ==============================================================

class RegistryManager(ABC):
    """Serializer registry management contract."""

    @abstractmethod
    def register(
        self,
        serializer: BaseSerializer,
    ) -> Any:
        """Register a serializer."""

    @abstractmethod
    def unregister(
        self,
        name: SerializerName,
    ) -> Any:
        """Unregister a serializer."""

    @abstractmethod
    def contains(
        self,
        name: SerializerName,
    ) -> bool:
        """Check whether a serializer exists."""

    @abstractmethod
    def clear(
        self,
    ) -> None:
        """Clear registrations."""

    @abstractmethod
    def serializers(
        self,
    ) -> list[SerializerName]:
        """Return registered serializer names."""

    def get(
        self,
        name: SerializerName,
        default: Any = None,
    ) -> Any:
        """Optional registry lookup."""
        return default

    def aliases(
        self,
        name: SerializerName,
    ) -> list[str]:
        """Return aliases for a serializer."""
        return []

    def set_default(
        self,
        purpose: str,
        name: SerializerName,
    ) -> None:
        """Configure a default serializer."""
        raise NotImplementedError

    def get_default(
        self,
        purpose: str = "general",
    ) -> Any:
        """Return a configured default serializer."""
        return None


class RegistryListener(ABC):
    """Observer for registry changes."""

    @abstractmethod
    def registry_changed(
        self,
        event: str,
        payload: Mapping[str, Any],
    ) -> None:
        """Handle a registry event."""


# ==============================================================
# Configuration
# ==============================================================

class Configurable(ABC):
    """Configurable component contract."""

    @abstractmethod
    def configure(
        self,
        options: Mapping[str, Any],
    ) -> None:
        """Apply configuration."""

    @abstractmethod
    def configuration(
        self,
    ) -> Mapping[str, Any]:
        """Return current configuration."""

    def configure_one(
        self,
        name: str,
        value: Any,
    ) -> None:
        """Convenience configuration helper."""
        self.configure(
            {name: value}
        )


class OptionProvider(ABC):
    """Provider for supported configuration options."""

    @abstractmethod
    def options(
        self,
    ) -> Mapping[str, Any]:
        """Return option metadata."""

    def supports_option(
        self,
        name: str,
    ) -> bool:
        return name in self.options()


# ==============================================================
# Lifecycle
# ==============================================================

class Lifecycle(ABC):
    """Lifecycle management contract."""

    @abstractmethod
    def initialize(self) -> None:
        """Initialize resources."""

    @abstractmethod
    def shutdown(self) -> None:
        """Release resources."""

    @abstractmethod
    def reset(self) -> None:
        """Reset runtime state."""

    def reopen(self) -> None:
        """Reopen a previously closed component."""
        self.initialize()


class Startable(ABC):
    """Startable component."""

    @abstractmethod
    def start(self) -> None:
        """Start component."""


class Stoppable(ABC):
    """Stoppable component."""

    @abstractmethod
    def stop(self) -> None:
        """Stop component."""


class Disposable(ABC):
    """Resource disposal contract."""

    @abstractmethod
    def dispose(self) -> None:
        """Release all resources."""


# ==============================================================
# Statistics
# ==============================================================

class StatisticsProvider(ABC):
    """Runtime statistics provider."""

    @abstractmethod
    def statistics(
        self,
    ) -> Mapping[str, Any]:
        """Return runtime statistics."""


class MetricsProvider(ABC):
    """Metrics provider."""

    @abstractmethod
    def metrics(
        self,
    ) -> Mapping[str, Any]:
        """Return metrics."""

    def metric(
        self,
        name: str,
        default: Any = None,
    ) -> Any:
        return self.metrics().get(
            name,
            default,
        )


class PerformanceProvider(ABC):
    """Performance information provider."""

    @abstractmethod
    def performance(
        self,
    ) -> Mapping[str, Any]:
        """Return performance measurements."""


# ==============================================================
# Validation
# ==============================================================

class Validator(ABC):
    """General validation contract."""

    @abstractmethod
    def validate(
        self,
        value: Any,
    ) -> bool:
        """Validate a value."""

    def validate_or_raise(
        self,
        value: Any,
    ) -> Any:
        if not self.validate(value):
            raise ValueError(
                "Validation failed."
            )
        return value


class SerializableValidator(ABC):
    """Validation for serializable values."""

    @abstractmethod
    def can_serialize(
        self,
        value: Any,
    ) -> bool:
        """Determine whether a value is serializable."""


class DeserializableValidator(ABC):
    """Validation for serialized data."""

    @abstractmethod
    def can_deserialize(
        self,
        data: SerializedData,
    ) -> bool:
        """Determine whether data is deserializable."""


class SchemaValidator(ABC):
    """Schema-based validation contract."""

    @abstractmethod
    def validate_schema(
        self,
        value: Any,
        schema: BaseSchema,
    ) -> bool:
        """Validate against a schema."""


# ==============================================================
# Discovery
# ==============================================================

class Discoverable(ABC):
    """Discoverable component."""

    @property
    @abstractmethod
    def identifier(self) -> str:
        """Unique identifier."""

    @property
    @abstractmethod
    def description(self) -> str:
        """Component description."""


class CapabilityProvider(ABC):
    """Component capability provider."""

    @abstractmethod
    def capabilities(self) -> set[str]:
        """Return supported capabilities."""

    def supports_capability(
        self,
        capability: str,
    ) -> bool:
        return capability in self.capabilities()


class ExtensionProvider(ABC):
    """File-extension discovery contract."""

    @property
    @abstractmethod
    def supported_extensions(
        self,
    ) -> Sequence[str]:
        """Return supported file extensions."""

    def supports_extension(
        self,
        extension: str,
    ) -> bool:
        normalized = str(
            extension
        ).lower()

        if not normalized.startswith("."):
            normalized = "." + normalized

        return normalized in {
            str(item).lower()
            for item in self.supported_extensions
        }


class MediaTypeProvider(ABC):
    """MIME/media type discovery contract."""

    @property
    @abstractmethod
    def media_types(
        self,
    ) -> Sequence[str]:
        """Return supported media types."""

    def supports_media_type(
        self,
        media_type: str,
    ) -> bool:
        return (
            str(media_type).lower()
            in {
                str(item).lower()
                for item in self.media_types
            }
        )


# ==============================================================
# Monitoring
# ==============================================================

class HealthCheck(ABC):
    """Health monitoring contract."""

    @abstractmethod
    def healthy(self) -> bool:
        """Return component health state."""

    def health_details(
        self,
    ) -> Mapping[str, Any]:
        return {
            "healthy": self.healthy()
        }


class ReadinessCheck(ABC):
    """Readiness contract."""

    @abstractmethod
    def ready(self) -> bool:
        """Return readiness state."""


class LivenessCheck(ABC):
    """Liveness contract."""

    @abstractmethod
    def alive(self) -> bool:
        """Return liveness state."""


# ==============================================================
# Export / Import
# ==============================================================

class Exportable(ABC):
    """Export runtime state."""

    @abstractmethod
    def export(
        self,
    ) -> Mapping[str, Any]:
        """Export component state."""


class Importable(ABC):
    """Import runtime state."""

    @abstractmethod
    def import_data(
        self,
        data: Mapping[str, Any],
    ) -> None:
        """Import component state."""


class SnapshotProvider(ABC):
    """Snapshot provider."""

    @abstractmethod
    def snapshot(self) -> Mapping[str, Any]:
        """Create a snapshot."""

    @abstractmethod
    def restore(
        self,
        snapshot: Mapping[str, Any],
    ) -> None:
        """Restore a snapshot."""


# ==============================================================
# Diagnostics
# ==============================================================

class DiagnosticProvider(ABC):
    """Diagnostic information provider."""

    @abstractmethod
    def diagnostics(
        self,
    ) -> Mapping[str, Any]:
        """Return diagnostics."""


class RuntimeInformationProvider(ABC):
    """Runtime information provider."""

    @abstractmethod
    def runtime_information(
        self,
    ) -> Mapping[str, Any]:
        """Return runtime information."""


class RuntimeSummaryProvider(ABC):
    """Runtime summary provider."""

    @abstractmethod
    def summary(
        self,
    ) -> Mapping[str, Any]:
        """Return concise runtime summary."""


# ==============================================================
# Identity / Version
# ==============================================================

class VersionProvider(ABC):
    """Component version provider."""

    @property
    @abstractmethod
    def version(self) -> str:
        """Component version."""


class NameProvider(ABC):
    """Component name provider."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Component name."""


class IdentifierProvider(ABC):
    """Stable identifier provider."""

    @property
    @abstractmethod
    def identifier(self) -> str:
        """Stable identifier."""


# ==============================================================
# Utilities
# ==============================================================

class Cloneable(ABC):
    """Cloneable component."""

    @abstractmethod
    def clone(self) -> "Cloneable":
        """Create an independent clone."""


class Resettable(ABC):
    """Resettable component."""

    @abstractmethod
    def reset(self) -> None:
        """Reset internal state."""


class ContextAware(ABC):
    """Component that accepts runtime context."""

    @abstractmethod
    def with_context(
        self,
        context: SerializationContext,
    ) -> "ContextAware":
        """Return a context-aware view."""


class Transactional(ABC):
    """Transactional operation provider."""

    @abstractmethod
    def begin(self) -> Any:
        """Begin a transaction."""

    @abstractmethod
    def commit(self) -> None:
        """Commit the current transaction."""

    @abstractmethod
    def rollback(self) -> None:
        """Rollback the current transaction."""


# ==============================================================
# Compatibility Contracts
# ==============================================================

class Serializable(ABC):
    """Object-owned serialization contract."""

    @abstractmethod
    def to_serializable(
        self,
        *,
        context: SerializationContext | None = None,
    ) -> Any:
        """Convert the object into serializable data."""


class Deserializable(ABC):
    """Class-owned deserialization contract."""

    @classmethod
    @abstractmethod
    def from_serialized(
        cls,
        data: Any,
        *,
        context: SerializationContext | None = None,
    ) -> Any:
        """Construct an object from serialized data."""


class Encodable(ABC):
    """Generic encoding contract."""

    @abstractmethod
    def encode(
        self,
        value: Any,
    ) -> SerializedData:
        """Encode a value."""


class Decodable(ABC):
    """Generic decoding contract."""

    @abstractmethod
    def decode(
        self,
        data: SerializedData,
    ) -> Any:
        """Decode data."""


# ==============================================================
# Composite Interface Helpers
# ==============================================================

class EnterpriseCodec(
    BaseCodec,
    StreamSerializer,
    StreamDeserializer,
    FileSerializer,
    FileDeserializer,
    RequestSerializer,
    RequestDeserializer,
    Configurable,
    Lifecycle,
    StatisticsProvider,
    HealthCheck,
    CapabilityProvider,
    Discoverable,
    VersionProvider,
    Cloneable,
    Resettable,
):
    """
    Full enterprise codec contract.

    Concrete codecs do not have to inherit this class directly; it is
    provided as a strong contract for implementations that want all
    enterprise capabilities.
    """

    pass


class EnterpriseSerializer(
    BaseSerializer,
    StreamSerializer,
    FileSerializer,
    RequestSerializer,
    Configurable,
    Lifecycle,
    StatisticsProvider,
    HealthCheck,
    CapabilityProvider,
    Discoverable,
    VersionProvider,
    Cloneable,
    Resettable,
):
    """Full enterprise serializer contract."""

    pass


class EnterpriseDeserializer(
    BaseDeserializer,
    StreamDeserializer,
    FileDeserializer,
    RequestDeserializer,
    Configurable,
    Lifecycle,
    StatisticsProvider,
    HealthCheck,
    CapabilityProvider,
    Discoverable,
    VersionProvider,
    Cloneable,
    Resettable,
):
    """Full enterprise deserializer contract."""

    pass


# ==============================================================
# Contract Inspection Helpers
# ==============================================================

def required_serializer_methods() -> tuple[str, ...]:
    """Return the minimum serializer method contract."""
    return (
        "serialize",
    )


def required_deserializer_methods() -> tuple[str, ...]:
    """Return the minimum deserializer method contract."""
    return (
        "deserialize",
    )


def required_codec_methods() -> tuple[str, ...]:
    """Return the minimum combined codec contract."""
    return (
        "serialize",
        "deserialize",
    )


def inspect_interface(
    component: Any,
) -> dict[str, Any]:
    """Inspect implemented serialization capabilities."""
    result = {
        "type": type(component).__name__,
        "module": type(component).__module__,
        "serializer":
            callable(
                getattr(
                    component,
                    "serialize",
                    None,
                )
            ),
        "deserializer":
            callable(
                getattr(
                    component,
                    "deserialize",
                    None,
                )
            ),
        "stream_serializer":
            callable(
                getattr(
                    component,
                    "serialize_to_stream",
                    None,
                )
            ),
        "stream_deserializer":
            callable(
                getattr(
                    component,
                    "deserialize_from_stream",
                    None,
                )
            ),
        "file_serializer":
            callable(
                getattr(
                    component,
                    "serialize_to_file",
                    None,
                )
            ),
        "file_deserializer":
            callable(
                getattr(
                    component,
                    "deserialize_from_file",
                    None,
                )
            ),
        "async_serializer":
            callable(
                getattr(
                    component,
                    "serialize_async",
                    None,
                )
            ),
        "async_deserializer":
            callable(
                getattr(
                    component,
                    "deserialize_async",
                    None,
                )
            ),
        "configurable":
            callable(
                getattr(
                    component,
                    "configure",
                    None,
                )
            ),
        "lifecycle":
            all(
                callable(
                    getattr(
                        component,
                        operation,
                        None,
                    )
                )
                for operation in (
                    "initialize",
                    "shutdown",
                    "reset",
                )
            ),
        "health":
            callable(
                getattr(
                    component,
                    "healthy",
                    None,
                )
            )
            or callable(
                getattr(
                    component,
                    "health",
                    None,
                )
            ),
    }

    capabilities = getattr(
        component,
        "capabilities",
        None,
    )

    if callable(capabilities):
        try:
            result["capabilities"] = sorted(
                capabilities()
            )
        except Exception:
            result["capabilities"] = []

    return result


def validate_interface(
    component: Any,
    *,
    require_serializer: bool = False,
    require_deserializer: bool = False,
) -> tuple[bool, list[str]]:
    """Validate a component against the basic AURA contract."""
    errors: list[str] = []

    if component is None:
        return False, [
            "component cannot be None"
        ]

    if (
        require_serializer
        and not callable(
            getattr(
                component,
                "serialize",
                None,
            )
        )
    ):
        errors.append(
            "component does not provide serialize()"
        )

    if (
        require_deserializer
        and not callable(
            getattr(
                component,
                "deserialize",
                None,
            )
        )
    ):
        errors.append(
            "component does not provide deserialize()"
        )

    name = getattr(
        component,
        "name",
        None,
    )

    if name is None:
        errors.append(
            "component does not expose name"
        )

    return not errors, errors


# ==============================================================
# Public API
# ==============================================================

__all__ = [
    "SerializedData",
    "FormatName",
    "SerializerName",
    "SerializationContext",
    "InputStream",
    "OutputStream",

    "BaseSerializer",
    "BaseDeserializer",
    "BaseCodec",

    "StreamSerializer",
    "StreamDeserializer",
    "FileSerializer",
    "FileDeserializer",

    "AsyncSerializer",
    "AsyncDeserializer",
    "AsyncStreamSerializer",
    "AsyncStreamDeserializer",
    "AsyncFileSerializer",
    "AsyncFileDeserializer",

    "RequestSerializer",
    "RequestDeserializer",
    "ResponseSerializer",
    "ResponseDeserializer",

    "BaseSchema",
    "SchemaProvider",

    "Compressor",
    "Decompressor",
    "CompressionProvider",

    "Encryptor",
    "Decryptor",
    "EncryptionProvider",

    "Pipeline",
    "PipelineStage",
    "Middleware",

    "RegistryManager",
    "RegistryListener",

    "Configurable",
    "OptionProvider",

    "Lifecycle",
    "Startable",
    "Stoppable",
    "Disposable",

    "StatisticsProvider",
    "MetricsProvider",
    "PerformanceProvider",

    "Validator",
    "SerializableValidator",
    "DeserializableValidator",
    "SchemaValidator",

    "Discoverable",
    "CapabilityProvider",
    "ExtensionProvider",
    "MediaTypeProvider",

    "HealthCheck",
    "ReadinessCheck",
    "LivenessCheck",

    "Exportable",
    "Importable",
    "SnapshotProvider",

    "DiagnosticProvider",
    "RuntimeInformationProvider",
    "RuntimeSummaryProvider",

    "VersionProvider",
    "NameProvider",
    "IdentifierProvider",

    "Cloneable",
    "Resettable",
    "ContextAware",
    "Transactional",

    "Serializable",
    "Deserializable",
    "Encodable",
    "Decodable",

    "EnterpriseCodec",
    "EnterpriseSerializer",
    "EnterpriseDeserializer",

    "required_serializer_methods",
    "required_deserializer_methods",
    "required_codec_methods",
    "inspect_interface",
    "validate_interface",
]