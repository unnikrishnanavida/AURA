"""
AURA Framework - Serialization Models.

Canonical request, response, configuration, metadata, batch, file,
stream, validation, diagnostics, metrics, and lifecycle models used by
the AURA serialization subsystem.

These models are intentionally format-neutral. Concrete codecs consume
the models while retaining responsibility for their own encoding rules.
"""

from __future__ import annotations

import copy
import hashlib
import time

from dataclasses import (
    asdict,
    dataclass,
    field,
    replace,
)
from datetime import datetime, timezone
from pathlib import Path
from typing import (
    Any,
    Iterable,
    Mapping,
    Sequence,
)


# ==============================================================
# Shared helpers
# ==============================================================

def utc_now() -> datetime:
    """Return the current UTC timestamp."""
    return datetime.now(
        timezone.utc
    )


def iso_timestamp(
    value: datetime | None = None,
) -> str:
    """Return an ISO-8601 UTC timestamp."""
    current = value or utc_now()

    if current.tzinfo is None:
        current = current.replace(
            tzinfo=timezone.utc
        )

    return current.astimezone(
        timezone.utc
    ).isoformat()


def data_size(
    value: Any,
    *,
    encoding: str = "utf-8",
) -> int | None:
    """Best-effort byte-size calculation."""
    if value is None:
        return 0

    if isinstance(value, bytes):
        return len(value)

    if isinstance(value, str):
        return len(
            value.encode(
                encoding
            )
        )

    try:
        return len(value)
    except Exception:
        return None


def data_digest(
    value: Any,
    *,
    encoding: str = "utf-8",
    algorithm: str = "sha256",
) -> str:
    """Create a deterministic digest for serialized data."""
    if isinstance(value, str):
        raw = value.encode(
            encoding
        )
    elif isinstance(value, bytes):
        raw = value
    else:
        raw = repr(value).encode(
            encoding
        )

    digest = hashlib.new(
        algorithm
    )
    digest.update(raw)
    return digest.hexdigest()


def copy_metadata(
    metadata: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Deep-copy metadata into a mutable dictionary."""
    return copy.deepcopy(
        dict(metadata or {})
    )


# ==============================================================
# Serialization Request
# ==============================================================

@dataclass
class SerializationRequest:
    """Request sent to a serializer codec."""

    value: Any
    format: str
    encoding: str = "utf-8"
    compress: bool = False
    encrypt: bool = False
    compression: str | None = None
    encryption: str | None = None
    compression_level: int | None = None
    encryption_key: bytes | str | None = None
    context: dict[str, Any] = field(
        default_factory=dict
    )
    metadata: dict[str, Any] = field(
        default_factory=dict
    )
    options: dict[str, Any] = field(
        default_factory=dict
    )
    request_id: str | None = None
    timestamp: datetime = field(
        default_factory=utc_now
    )

    def __post_init__(self) -> None:
        self.format = str(
            self.format
        ).strip().lower()

        if not self.format:
            raise ValueError(
                "format cannot be empty"
            )

        self.context = copy_metadata(
            self.context
        )

        self.metadata = copy_metadata(
            self.metadata
        )

        self.options = copy_metadata(
            self.options
        )

    @property
    def created_at(self) -> str:
        return iso_timestamp(
            self.timestamp
        )

    def option(
        self,
        name: str,
        default: Any = None,
    ) -> Any:
        return self.options.get(
            name,
            default,
        )

    def with_option(
        self,
        name: str,
        value: Any,
    ) -> "SerializationRequest":
        options = dict(
            self.options
        )
        options[name] = value

        return replace(
            self,
            options=options,
        )

    def with_context(
        self,
        **values: Any,
    ) -> "SerializationRequest":
        context = dict(
            self.context
        )
        context.update(values)

        return replace(
            self,
            context=context,
        )

    def with_metadata(
        self,
        **values: Any,
    ) -> "SerializationRequest":
        metadata = dict(
            self.metadata
        )
        metadata.update(values)

        return replace(
            self,
            metadata=metadata,
        )

    def copy(self) -> "SerializationRequest":
        return copy.deepcopy(
            self
        )

    def as_dict(
        self,
        *,
        include_sensitive: bool = False,
    ) -> dict[str, Any]:
        result = {
            "format": self.format,
            "encoding": self.encoding,
            "compress": self.compress,
            "encrypt": self.encrypt,
            "compression": self.compression,
            "encryption": self.encryption,
            "compression_level":
                self.compression_level,
            "context":
                copy_metadata(self.context),
            "metadata":
                copy_metadata(self.metadata),
            "options":
                copy_metadata(self.options),
            "request_id":
                self.request_id,
            "timestamp":
                self.created_at,
        }

        if include_sensitive:
            result[
                "encryption_key"
            ] = self.encryption_key

        return result


# ==============================================================
# Serialization Response
# ==============================================================

@dataclass
class SerializationResponse:
    """Response produced by a serializer codec."""

    data: str | bytes
    format: str
    encoding: str = "utf-8"
    compressed: bool = False
    encrypted: bool = False
    metadata: dict[str, Any] = field(
        default_factory=dict
    )
    request_id: str | None = None
    duration: float = 0.0
    created_at: datetime = field(
        default_factory=utc_now
    )
    success: bool = True
    error: str | None = None
    size: int | None = None
    digest: str | None = None

    def __post_init__(self) -> None:
        self.format = str(
            self.format
        ).strip().lower()

        self.metadata = copy_metadata(
            self.metadata
        )

        if self.size is None:
            self.size = data_size(
                self.data,
                encoding=self.encoding,
            )

        if self.digest is None:
            self.digest = data_digest(
                self.data,
                encoding=self.encoding,
            )

    @property
    def timestamp(self) -> str:
        return iso_timestamp(
            self.created_at
        )

    def text(
        self,
    ) -> str:
        if isinstance(
            self.data,
            bytes,
        ):
            return self.data.decode(
                self.encoding
            )

        return self.data

    def bytes(
        self,
    ) -> bytes:
        if isinstance(
            self.data,
            str,
        ):
            return self.data.encode(
                self.encoding
            )

        return self.data

    def as_dict(
        self,
    ) -> dict[str, Any]:
        return {
            "format": self.format,
            "encoding": self.encoding,
            "compressed": self.compressed,
            "encrypted": self.encrypted,
            "metadata":
                copy_metadata(self.metadata),
            "request_id":
                self.request_id,
            "duration":
                self.duration,
            "created_at":
                self.timestamp,
            "success":
                self.success,
            "error":
                self.error,
            "size":
                self.size,
            "digest":
                self.digest,
        }

    def with_metadata(
        self,
        **values: Any,
    ) -> "SerializationResponse":
        metadata = dict(
            self.metadata
        )
        metadata.update(values)

        return replace(
            self,
            metadata=metadata,
        )


# ==============================================================
# Deserialization Request
# ==============================================================

@dataclass
class DeserializationRequest:
    """Request sent to a deserializer codec."""

    data: str | bytes
    format: str
    encoding: str = "utf-8"
    compressed: bool = False
    encrypted: bool = False
    compression: str | None = None
    encryption: str | None = None
    compression_level: int | None = None
    encryption_key: bytes | str | None = None
    context: dict[str, Any] = field(
        default_factory=dict
    )
    metadata: dict[str, Any] = field(
        default_factory=dict
    )
    options: dict[str, Any] = field(
        default_factory=dict
    )
    request_id: str | None = None
    timestamp: datetime = field(
        default_factory=utc_now
    )

    def __post_init__(self) -> None:
        self.format = str(
            self.format
        ).strip().lower()

        if not self.format:
            raise ValueError(
                "format cannot be empty"
            )

        self.context = copy_metadata(
            self.context
        )

        self.metadata = copy_metadata(
            self.metadata
        )

        self.options = copy_metadata(
            self.options
        )

    @property
    def created_at(self) -> str:
        return iso_timestamp(
            self.timestamp
        )

    @property
    def size(self) -> int | None:
        return data_size(
            self.data,
            encoding=self.encoding,
        )

    def option(
        self,
        name: str,
        default: Any = None,
    ) -> Any:
        return self.options.get(
            name,
            default,
        )

    def with_option(
        self,
        name: str,
        value: Any,
    ) -> "DeserializationRequest":
        options = dict(
            self.options
        )
        options[name] = value

        return replace(
            self,
            options=options,
        )

    def with_context(
        self,
        **values: Any,
    ) -> "DeserializationRequest":
        context = dict(
            self.context
        )
        context.update(values)

        return replace(
            self,
            context=context,
        )

    def copy(self) -> "DeserializationRequest":
        return copy.deepcopy(
            self
        )

    def as_dict(
        self,
        *,
        include_data: bool = False,
        include_sensitive: bool = False,
    ) -> dict[str, Any]:
        result = {
            "format": self.format,
            "encoding": self.encoding,
            "compressed": self.compressed,
            "encrypted": self.encrypted,
            "compression": self.compression,
            "encryption": self.encryption,
            "compression_level":
                self.compression_level,
            "context":
                copy_metadata(self.context),
            "metadata":
                copy_metadata(self.metadata),
            "options":
                copy_metadata(self.options),
            "request_id":
                self.request_id,
            "timestamp":
                self.created_at,
            "size":
                self.size,
        }

        if include_data:
            result["data"] = self.data

        if include_sensitive:
            result[
                "encryption_key"
            ] = self.encryption_key

        return result


# ==============================================================
# Deserialization Response
# ==============================================================

@dataclass
class DeserializationResponse:
    """Response produced by a deserializer codec."""

    value: Any
    metadata: dict[str, Any] = field(
        default_factory=dict
    )
    valid: bool = True
    format: str | None = None
    request_id: str | None = None
    duration: float = 0.0
    created_at: datetime = field(
        default_factory=utc_now
    )
    error: str | None = None
    warnings: list[str] = field(
        default_factory=list
    )
    source_size: int | None = None
    digest: str | None = None

    def __post_init__(self) -> None:
        self.metadata = copy_metadata(
            self.metadata
        )
        self.warnings = list(
            self.warnings
        )

    @property
    def success(self) -> bool:
        return (
            self.valid
            and self.error is None
        )

    @property
    def timestamp(self) -> str:
        return iso_timestamp(
            self.created_at
        )

    def add_warning(
        self,
        message: str,
    ) -> None:
        self.warnings.append(
            str(message)
        )

    def as_dict(
        self,
        *,
        include_value: bool = False,
    ) -> dict[str, Any]:
        result = {
            "metadata":
                copy_metadata(self.metadata),
            "valid":
                self.valid,
            "format":
                self.format,
            "request_id":
                self.request_id,
            "duration":
                self.duration,
            "created_at":
                self.timestamp,
            "error":
                self.error,
            "warnings":
                list(self.warnings),
            "source_size":
                self.source_size,
            "digest":
                self.digest,
        }

        if include_value:
            result["value"] = self.value

        return result


# ==============================================================
# Generic Operation Result
# ==============================================================

@dataclass
class OperationResult:
    """Generic result for serialization operations."""

    operation: str
    success: bool
    format: str | None = None
    value: Any = None
    data: str | bytes | None = None
    error: str | None = None
    warnings: list[str] = field(
        default_factory=list
    )
    metadata: dict[str, Any] = field(
        default_factory=dict
    )
    duration: float = 0.0
    started_at: datetime = field(
        default_factory=utc_now
    )
    finished_at: datetime | None = None

    @property
    def elapsed(self) -> float:
        if self.finished_at is None:
            return self.duration

        return (
            self.finished_at
            - self.started_at
        ).total_seconds()

    def finish(
        self,
        *,
        success: bool = True,
        error: str | None = None,
    ) -> "OperationResult":
        self.success = success
        self.error = error
        self.finished_at = utc_now()

        self.duration = (
            self.finished_at
            - self.started_at
        ).total_seconds()

        return self

    def add_warning(
        self,
        message: str,
    ) -> None:
        self.warnings.append(
            str(message)
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "operation":
                self.operation,
            "success":
                self.success,
            "format":
                self.format,
            "error":
                self.error,
            "warnings":
                list(self.warnings),
            "metadata":
                copy_metadata(self.metadata),
            "duration":
                self.duration,
            "started_at":
                iso_timestamp(
                    self.started_at
                ),
            "finished_at":
                (
                    iso_timestamp(
                        self.finished_at
                    )
                    if self.finished_at
                    else None
                ),
        }


# ==============================================================
# Batch Models
# ==============================================================

@dataclass
class BatchSerializationRequest:
    """Request for serializing multiple values."""

    values: list[Any]
    format: str
    encoding: str = "utf-8"
    context: dict[str, Any] = field(
        default_factory=dict
    )
    options: dict[str, Any] = field(
        default_factory=dict
    )
    stop_on_error: bool = True
    request_id: str | None = None

    def __post_init__(self) -> None:
        self.values = list(
            self.values
        )
        self.format = str(
            self.format
        ).strip().lower()
        self.context = copy_metadata(
            self.context
        )
        self.options = copy_metadata(
            self.options
        )

    @property
    def count(self) -> int:
        return len(
            self.values
        )

    def copy(self) -> "BatchSerializationRequest":
        return copy.deepcopy(
            self
        )


@dataclass
class BatchDeserializationRequest:
    """Request for deserializing multiple payloads."""

    values: list[str | bytes]
    format: str
    encoding: str = "utf-8"
    context: dict[str, Any] = field(
        default_factory=dict
    )
    options: dict[str, Any] = field(
        default_factory=dict
    )
    stop_on_error: bool = True
    request_id: str | None = None

    def __post_init__(self) -> None:
        self.values = list(
            self.values
        )
        self.format = str(
            self.format
        ).strip().lower()
        self.context = copy_metadata(
            self.context
        )
        self.options = copy_metadata(
            self.options
        )

    @property
    def count(self) -> int:
        return len(
            self.values
        )


@dataclass
class BatchItemResult:
    """Result for one item in a batch."""

    index: int
    success: bool
    value: Any = None
    data: str | bytes | None = None
    error: str | None = None
    duration: float = 0.0
    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def as_dict(self) -> dict[str, Any]:
        return {
            "index":
                self.index,
            "success":
                self.success,
            "error":
                self.error,
            "duration":
                self.duration,
            "metadata":
                copy_metadata(self.metadata),
        }


@dataclass
class BatchOperationResult:
    """Aggregate result for a batch operation."""

    operation: str
    format: str
    items: list[BatchItemResult] = field(
        default_factory=list
    )
    success: bool = True
    duration: float = 0.0
    error: str | None = None

    @property
    def count(self) -> int:
        return len(
            self.items
        )

    @property
    def successful_count(self) -> int:
        return sum(
            1
            for item in self.items
            if item.success
        )

    @property
    def failed_count(self) -> int:
        return (
            self.count
            - self.successful_count
        )

    def add(
        self,
        item: BatchItemResult,
    ) -> None:
        self.items.append(
            item
        )

        if not item.success:
            self.success = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "operation":
                self.operation,
            "format":
                self.format,
            "count":
                self.count,
            "successful_count":
                self.successful_count,
            "failed_count":
                self.failed_count,
            "success":
                self.success,
            "duration":
                self.duration,
            "error":
                self.error,
            "items":
                [
                    item.as_dict()
                    for item in self.items
                ],
        }


# ==============================================================
# File Models
# ==============================================================

@dataclass
class FileSerializationRequest:
    """Serialization request targeting a filesystem path."""

    value: Any
    path: str | Path
    format: str | None = None
    encoding: str = "utf-8"
    overwrite: bool = True
    create_parent: bool = True
    atomic: bool = False
    context: dict[str, Any] = field(
        default_factory=dict
    )
    options: dict[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        self.path = Path(
            self.path
        )
        self.context = copy_metadata(
            self.context
        )
        self.options = copy_metadata(
            self.options
        )


@dataclass
class FileDeserializationRequest:
    """Deserialization request targeting a filesystem path."""

    path: str | Path
    format: str | None = None
    encoding: str = "utf-8"
    context: dict[str, Any] = field(
        default_factory=dict
    )
    options: dict[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        self.path = Path(
            self.path
        )
        self.context = copy_metadata(
            self.context
        )
        self.options = copy_metadata(
            self.options
        )


@dataclass
class FileOperationResult:
    """Result of a file operation."""

    path: Path
    operation: str
    success: bool
    format: str | None = None
    size: int | None = None
    duration: float = 0.0
    error: str | None = None
    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def as_dict(self) -> dict[str, Any]:
        return {
            "path":
                str(self.path),
            "operation":
                self.operation,
            "success":
                self.success,
            "format":
                self.format,
            "size":
                self.size,
            "duration":
                self.duration,
            "error":
                self.error,
            "metadata":
                copy_metadata(self.metadata),
        }


# ==============================================================
# Stream Models
# ==============================================================

@dataclass
class StreamSerializationRequest:
    """Serialization request targeting a stream."""

    value: Any
    stream: Any
    format: str
    context: dict[str, Any] = field(
        default_factory=dict
    )
    options: dict[str, Any] = field(
        default_factory=dict
    )


@dataclass
class StreamDeserializationRequest:
    """Deserialization request targeting a stream."""

    stream: Any
    format: str
    context: dict[str, Any] = field(
        default_factory=dict
    )
    options: dict[str, Any] = field(
        default_factory=dict
    )


# ==============================================================
# Validation Models
# ==============================================================

@dataclass
class ValidationResult:
    """Structured validation result."""

    valid: bool
    errors: list[str] = field(
        default_factory=list
    )
    warnings: list[str] = field(
        default_factory=list
    )
    format: str | None = None
    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def add_error(
        self,
        message: str,
    ) -> None:
        self.errors.append(
            str(message)
        )
        self.valid = False

    def add_warning(
        self,
        message: str,
    ) -> None:
        self.warnings.append(
            str(message)
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "valid":
                self.valid,
            "errors":
                list(self.errors),
            "warnings":
                list(self.warnings),
            "format":
                self.format,
            "metadata":
                copy_metadata(self.metadata),
        }


@dataclass
class SchemaValidationResult(
    ValidationResult
):
    """Validation result with schema information."""

    schema_name: str | None = None
    schema_version: str | None = None

    def as_dict(self) -> dict[str, Any]:
        result = super().as_dict()

        result.update({
            "schema_name":
                self.schema_name,
            "schema_version":
                self.schema_version,
        })

        return result


# ==============================================================
# Codec Metadata
# ==============================================================

@dataclass
class CodecMetadata:
    """Descriptive metadata for a codec."""

    name: str
    format: str
    version: str = "1.0.0"
    description: str = ""
    extensions: tuple[str, ...] = ()
    media_types: tuple[str, ...] = ()
    capabilities: frozenset[str] = frozenset()
    aliases: tuple[str, ...] = ()
    priority: int = 0
    experimental: bool = False
    secure: bool = False
    deterministic: bool = False

    def __post_init__(self) -> None:
        self.name = str(
            self.name
        ).strip().lower()

        self.format = str(
            self.format
        ).strip().lower()

        self.extensions = tuple(
            self.extensions
        )

        self.media_types = tuple(
            self.media_types
        )

        self.aliases = tuple(
            self.aliases
        )

        self.capabilities = frozenset(
            self.capabilities
        )

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
            item.lower()
            for item in self.extensions
        }

    def supports_media_type(
        self,
        media_type: str,
    ) -> bool:
        return str(
            media_type
        ).lower() in {
            item.lower()
            for item in self.media_types
        }

    def as_dict(self) -> dict[str, Any]:
        return {
            "name":
                self.name,
            "format":
                self.format,
            "version":
                self.version,
            "description":
                self.description,
            "extensions":
                list(self.extensions),
            "media_types":
                list(self.media_types),
            "capabilities":
                sorted(
                    self.capabilities
                ),
            "aliases":
                list(self.aliases),
            "priority":
                self.priority,
            "experimental":
                self.experimental,
            "secure":
                self.secure,
            "deterministic":
                self.deterministic,
        }


# ==============================================================
# Capability Models
# ==============================================================

@dataclass(frozen=True)
class Capability:
    """One named codec capability."""

    name: str
    enabled: bool = True
    description: str = ""
    version: str | None = None

    def as_dict(self) -> dict[str, Any]:
        return {
            "name":
                self.name,
            "enabled":
                self.enabled,
            "description":
                self.description,
            "version":
                self.version,
        }


@dataclass
class CapabilityReport:
    """Collection of codec capabilities."""

    format: str
    capabilities: list[Capability] = field(
        default_factory=list
    )

    def add(
        self,
        capability: Capability,
    ) -> None:
        self.capabilities.append(
            capability
        )

    def supports(
        self,
        name: str,
    ) -> bool:
        return any(
            item.name == name
            and item.enabled
            for item in self.capabilities
        )

    def names(
        self,
    ) -> list[str]:
        return [
            item.name
            for item in self.capabilities
            if item.enabled
        ]

    def as_dict(self) -> dict[str, Any]:
        return {
            "format":
                self.format,
            "capabilities":
                [
                    item.as_dict()
                    for item in self.capabilities
                ],
        }


# ==============================================================
# Metrics Models
# ==============================================================

@dataclass
class OperationMetrics:
    """Metrics for a single serialization operation."""

    operation: str
    format: str
    count: int = 0
    failures: int = 0
    total_duration: float = 0.0
    minimum_duration: float | None = None
    maximum_duration: float | None = None
    input_bytes: int = 0
    output_bytes: int = 0

    @property
    def average_duration(self) -> float:
        if self.count <= 0:
            return 0.0

        return (
            self.total_duration
            / self.count
        )

    @property
    def success_rate(self) -> float:
        if self.count <= 0:
            return 1.0

        return (
            self.count
            - self.failures
        ) / self.count

    def record(
        self,
        duration: float,
        *,
        input_size: int | None = None,
        output_size: int | None = None,
        success: bool = True,
    ) -> None:
        self.count += 1
        self.total_duration += float(
            duration
        )

        if not success:
            self.failures += 1

        if (
            self.minimum_duration is None
            or duration < self.minimum_duration
        ):
            self.minimum_duration = duration

        if (
            self.maximum_duration is None
            or duration > self.maximum_duration
        ):
            self.maximum_duration = duration

        if input_size:
            self.input_bytes += int(
                input_size
            )

        if output_size:
            self.output_bytes += int(
                output_size
            )

    def as_dict(self) -> dict[str, Any]:
        return {
            "operation":
                self.operation,
            "format":
                self.format,
            "count":
                self.count,
            "failures":
                self.failures,
            "total_duration":
                self.total_duration,
            "average_duration":
                self.average_duration,
            "minimum_duration":
                self.minimum_duration,
            "maximum_duration":
                self.maximum_duration,
            "input_bytes":
                self.input_bytes,
            "output_bytes":
                self.output_bytes,
            "success_rate":
                self.success_rate,
        }


@dataclass
class MetricsSnapshot:
    """Point-in-time aggregate metrics."""

    captured_at: datetime = field(
        default_factory=utc_now
    )
    operations: list[OperationMetrics] = field(
        default_factory=list
    )

    @property
    def timestamp(self) -> str:
        return iso_timestamp(
            self.captured_at
        )

    def total_operations(self) -> int:
        return sum(
            item.count
            for item in self.operations
        )

    def total_failures(self) -> int:
        return sum(
            item.failures
            for item in self.operations
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "captured_at":
                self.timestamp,
            "total_operations":
                self.total_operations(),
            "total_failures":
                self.total_failures(),
            "operations":
                [
                    item.as_dict()
                    for item in self.operations
                ],
        }


# ==============================================================
# Health Models
# ==============================================================

@dataclass
class HealthStatus:
    """Structured health state."""

    healthy: bool
    status: str = "unknown"
    message: str | None = None
    checks: dict[str, bool] = field(
        default_factory=dict
    )
    details: dict[str, Any] = field(
        default_factory=dict
    )
    checked_at: datetime = field(
        default_factory=utc_now
    )

    @property
    def timestamp(self) -> str:
        return iso_timestamp(
            self.checked_at
        )

    def add_check(
        self,
        name: str,
        passed: bool,
    ) -> None:
        self.checks[
            str(name)
        ] = bool(passed)

        if not passed:
            self.healthy = False

    def as_dict(self) -> dict[str, Any]:
        return {
            "healthy":
                self.healthy,
            "status":
                self.status,
            "message":
                self.message,
            "checks":
                dict(self.checks),
            "details":
                copy_metadata(self.details),
            "checked_at":
                self.timestamp,
        }


# ==============================================================
# Lifecycle Models
# ==============================================================

@dataclass
class LifecycleState:
    """Lifecycle state for a serializer component."""

    initialized: bool = False
    running: bool = False
    closed: bool = False
    generation: int = 0
    initialized_at: datetime | None = None
    shutdown_at: datetime | None = None

    def initialize(self) -> None:
        self.initialized = True
        self.running = True
        self.closed = False
        self.generation += 1
        self.initialized_at = utc_now()

    def shutdown(self) -> None:
        self.running = False
        self.closed = True
        self.shutdown_at = utc_now()

    def reset(self) -> None:
        self.running = False
        self.initialized = False
        self.closed = False
        self.generation += 1

    def as_dict(self) -> dict[str, Any]:
        return {
            "initialized":
                self.initialized,
            "running":
                self.running,
            "closed":
                self.closed,
            "generation":
                self.generation,
            "initialized_at":
                (
                    iso_timestamp(
                        self.initialized_at
                    )
                    if self.initialized_at
                    else None
                ),
            "shutdown_at":
                (
                    iso_timestamp(
                        self.shutdown_at
                    )
                    if self.shutdown_at
                    else None
                ),
        }


# ==============================================================
# Configuration Models
# ==============================================================

@dataclass
class SerializationConfig:
    """Configuration shared by serialization operations."""

    format: str = "json"
    encoding: str = "utf-8"
    pretty: bool = False
    indent: int | None = None
    sort_keys: bool = False
    ensure_ascii: bool = False
    compress: bool = False
    compression: str | None = None
    compression_level: int | None = None
    encrypt: bool = False
    encryption: str | None = None
    timeout: float | None = None
    strict: bool = False
    validate: bool = True
    cache: bool = True
    metadata: dict[str, Any] = field(
        default_factory=dict
    )

    def __post_init__(self) -> None:
        self.format = str(
            self.format
        ).strip().lower()

        if self.indent is not None:
            self.indent = int(
                self.indent
            )

        if self.compression_level is not None:
            self.compression_level = int(
                self.compression_level
            )

        self.metadata = copy_metadata(
            self.metadata
        )

    def update(
        self,
        **values: Any,
    ) -> "SerializationConfig":
        current = asdict(
            self
        )
        current.update(values)

        return SerializationConfig(
            **current
        )

    def as_dict(self) -> dict[str, Any]:
        return asdict(
            self
        )


# ==============================================================
# Detection Models
# ==============================================================

@dataclass
class FormatCandidate:
    """One candidate returned by format detection."""

    format: str
    confidence: float
    source: str
    reason: str = ""
    codec: Any = None

    def __post_init__(self) -> None:
        self.format = str(
            self.format
        ).strip().lower()

        self.confidence = max(
            0.0,
            min(
                1.0,
                float(
                    self.confidence
                ),
            ),
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "format":
                self.format,
            "confidence":
                self.confidence,
            "source":
                self.source,
            "reason":
                self.reason,
        }


@dataclass
class FormatDetectionResult:
    """Result of automatic format detection."""

    selected: str | None
    candidates: list[FormatCandidate] = field(
        default_factory=list
    )
    input_name: str | None = None
    media_type: str | None = None
    detected_by: str | None = None

    @property
    def confident(self) -> bool:
        return bool(
            self.selected
            and self.candidates
            and self.candidates[0].confidence
            >= 0.75
        )

    def add(
        self,
        candidate: FormatCandidate,
    ) -> None:
        self.candidates.append(
            candidate
        )
        self.candidates.sort(
            key=lambda item:
                item.confidence,
            reverse=True,
        )

        if self.candidates:
            self.selected = (
                self.candidates[0].format
            )

    def as_dict(self) -> dict[str, Any]:
        return {
            "selected":
                self.selected,
            "input_name":
                self.input_name,
            "media_type":
                self.media_type,
            "detected_by":
                self.detected_by,
            "confident":
                self.confident,
            "candidates":
                [
                    item.as_dict()
                    for item in self.candidates
                ],
        }


# ==============================================================
# Snapshot Models
# ==============================================================

@dataclass
class SerializerSnapshot:
    """Serializable runtime snapshot of a serializer service."""

    name: str
    version: str
    default_format: str
    initialized: bool
    closed: bool
    configuration: dict[str, Any] = field(
        default_factory=dict
    )
    statistics: dict[str, Any] = field(
        default_factory=dict
    )
    metadata: dict[str, Any] = field(
        default_factory=dict
    )
    captured_at: datetime = field(
        default_factory=utc_now
    )

    @property
    def timestamp(self) -> str:
        return iso_timestamp(
            self.captured_at
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "name":
                self.name,
            "version":
                self.version,
            "default_format":
                self.default_format,
            "initialized":
                self.initialized,
            "closed":
                self.closed,
            "configuration":
                copy_metadata(
                    self.configuration
                ),
            "statistics":
                copy_metadata(
                    self.statistics
                ),
            "metadata":
                copy_metadata(
                    self.metadata
                ),
            "captured_at":
                self.timestamp,
        }


# ==============================================================
# Diagnostic Models
# ==============================================================

@dataclass
class DiagnosticMessage:
    """One diagnostic message."""

    level: str
    message: str
    code: str | None = None
    component: str | None = None
    details: dict[str, Any] = field(
        default_factory=dict
    )
    created_at: datetime = field(
        default_factory=utc_now
    )

    @property
    def timestamp(self) -> str:
        return iso_timestamp(
            self.created_at
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "level":
                self.level,
            "message":
                self.message,
            "code":
                self.code,
            "component":
                self.component,
            "details":
                copy_metadata(self.details),
            "created_at":
                self.timestamp,
        }


@dataclass
class DiagnosticReport:
    """Aggregate diagnostic report."""

    healthy: bool
    messages: list[DiagnosticMessage] = field(
        default_factory=list
    )
    statistics: dict[str, Any] = field(
        default_factory=dict
    )
    configuration: dict[str, Any] = field(
        default_factory=dict
    )
    generated_at: datetime = field(
        default_factory=utc_now
    )

    @property
    def timestamp(self) -> str:
        return iso_timestamp(
            self.generated_at
        )

    def add(
        self,
        message: DiagnosticMessage,
    ) -> None:
        self.messages.append(
            message
        )

        if message.level.lower() in {
            "error",
            "critical",
        }:
            self.healthy = False

    def errors(
        self,
    ) -> list[DiagnosticMessage]:
        return [
            item
            for item in self.messages
            if item.level.lower()
            in {
                "error",
                "critical",
            }
        ]

    def as_dict(self) -> dict[str, Any]:
        return {
            "healthy":
                self.healthy,
            "messages":
                [
                    item.as_dict()
                    for item in self.messages
                ],
            "statistics":
                copy_metadata(
                    self.statistics
                ),
            "configuration":
                copy_metadata(
                    self.configuration
                ),
            "generated_at":
                self.timestamp,
        }


# ==============================================================
# Exception / Error Models
# ==============================================================

@dataclass
class SerializationErrorInfo:
    """Structured error information."""

    error_type: str
    message: str
    operation: str | None = None
    format: str | None = None
    request_id: str | None = None
    retryable: bool = False
    details: dict[str, Any] = field(
        default_factory=dict
    )
    created_at: datetime = field(
        default_factory=utc_now
    )

    @property
    def timestamp(self) -> str:
        return iso_timestamp(
            self.created_at
        )

    def as_dict(self) -> dict[str, Any]:
        return {
            "error_type":
                self.error_type,
            "message":
                self.message,
            "operation":
                self.operation,
            "format":
                self.format,
            "request_id":
                self.request_id,
            "retryable":
                self.retryable,
            "details":
                copy_metadata(self.details),
            "created_at":
                self.timestamp,
        }

    @classmethod
    def from_exception(
        cls,
        exc: Exception,
        *,
        operation: str | None = None,
        format: str | None = None,
        request_id: str | None = None,
    ) -> "SerializationErrorInfo":
        return cls(
            error_type=type(
                exc
            ).__name__,
            message=str(
                exc
            ),
            operation=operation,
            format=format,
            request_id=request_id,
        )


# ==============================================================
# Utility Constructors
# ==============================================================

def make_serialization_request(
    value: Any,
    format: str,
    **kwargs: Any,
) -> SerializationRequest:
    """Create a serialization request."""
    return SerializationRequest(
        value=value,
        format=format,
        **kwargs,
    )


def make_deserialization_request(
    data: str | bytes,
    format: str,
    **kwargs: Any,
) -> DeserializationRequest:
    """Create a deserialization request."""
    return DeserializationRequest(
        data=data,
        format=format,
        **kwargs,
    )


def make_success_response(
    data: str | bytes,
    format: str,
    **kwargs: Any,
) -> SerializationResponse:
    """Create a successful serialization response."""
    return SerializationResponse(
        data=data,
        format=format,
        **kwargs,
    )


def make_success_deserialization_response(
    value: Any,
    **kwargs: Any,
) -> DeserializationResponse:
    """Create a successful deserialization response."""
    return DeserializationResponse(
        value=value,
        valid=True,
        **kwargs,
    )


def make_error_result(
    operation: str,
    error: Exception | str,
    *,
    format: str | None = None,
) -> OperationResult:
    """Create a failed operation result."""
    message = (
        str(error)
        if isinstance(
            error,
            Exception,
        )
        else error
    )

    return OperationResult(
        operation=operation,
        success=False,
        format=format,
        error=message,
    )


def merge_metadata(
    *metadata: Mapping[str, Any] | None,
) -> dict[str, Any]:
    """Merge metadata mappings from left to right."""
    result: dict[str, Any] = {}

    for item in metadata:
        if item:
            result.update(
                copy.deepcopy(
                    dict(item)
                )
            )

    return result


def clone_model(
    model: Any,
) -> Any:
    """Deep-clone a serialization model."""
    return copy.deepcopy(
        model
    )


# ==============================================================
# Public API
# ==============================================================

__all__ = [
    "utc_now",
    "iso_timestamp",
    "data_size",
    "data_digest",
    "copy_metadata",

    "SerializationRequest",
    "SerializationResponse",
    "DeserializationRequest",
    "DeserializationResponse",

    "OperationResult",

    "BatchSerializationRequest",
    "BatchDeserializationRequest",
    "BatchItemResult",
    "BatchOperationResult",

    "FileSerializationRequest",
    "FileDeserializationRequest",
    "FileOperationResult",

    "StreamSerializationRequest",
    "StreamDeserializationRequest",

    "ValidationResult",
    "SchemaValidationResult",

    "CodecMetadata",
    "Capability",
    "CapabilityReport",

    "OperationMetrics",
    "MetricsSnapshot",

    "HealthStatus",
    "LifecycleState",

    "SerializationConfig",

    "FormatCandidate",
    "FormatDetectionResult",

    "SerializerSnapshot",

    "DiagnosticMessage",
    "DiagnosticReport",

    "SerializationErrorInfo",

    "make_serialization_request",
    "make_deserialization_request",
    "make_success_response",
    "make_success_deserialization_response",
    "make_error_result",
    "merge_metadata",
    "clone_model",
]