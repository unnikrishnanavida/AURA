"""
AURA Framework - Enterprise Serializer.

High-level serialization service responsible for:
- codec lookup and registry integration
- direct serialization/deserialization
- request/response processing
- file and stream operations
- batch operations
- automatic format detection
- validation and capability inspection
- asynchronous dispatch
- fallback handling
- metrics and diagnostics
- lifecycle management
- configurable defaults

This module is the service layer. Concrete format implementations remain
inside their individual codec modules.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import threading
import time

from dataclasses import dataclass
from pathlib import Path
from typing import Any, IO, Iterable, Mapping, Sequence

from .constants import (
    DEFAULT_FORMAT,
    SerializationFormat,
)

from .exceptions import (
    SerializerNotFoundError,
)

from .interfaces import (
    BaseCodec,
)

from .models import (
    SerializationRequest,
    SerializationResponse,
    DeserializationRequest,
    DeserializationResponse,
)

from .registry import (
    serializer_registry,
)


@dataclass(frozen=True)
class SerializationOperation:
    """Metadata describing one completed serializer operation."""

    operation: str
    format: str
    duration: float
    input_size: int | None = None
    output_size: int | None = None
    success: bool = True
    error: str | None = None


class Serializer:
    """
    High-level AURA serialization service.

    The service deliberately delegates format-specific behavior to codecs
    registered in the central serialization registry.
    """

    def __init__(
        self,
        registry: Any = None,
        *,
        default_format: str | None = None,
    ) -> None:
        self._registry = (
            registry
            if registry is not None
            else serializer_registry
        )

        self._default_format = (
            default_format
            or DEFAULT_FORMAT.value
        )

        self._lock = threading.RLock()

        self._serialization_count = 0
        self._deserialization_count = 0
        self._serialization_time = 0.0
        self._deserialization_time = 0.0
        self._bytes_serialized = 0
        self._bytes_deserialized = 0
        self._failures = 0

        self._history: list[
            SerializationOperation
        ] = []

        self._history_limit = 256
        self._initialized = False
        self._closed = False

    # ==========================================================
    # Properties
    # ==========================================================

    @property
    def registry(self) -> Any:
        return self._registry

    @property
    def default_format(self) -> str:
        return self._default_format

    @property
    def initialized(self) -> bool:
        return self._initialized

    @property
    def closed(self) -> bool:
        return self._closed

    @property
    def serialization_count(self) -> int:
        return self._serialization_count

    @property
    def deserialization_count(self) -> int:
        return self._deserialization_count

    @property
    def serialization_time(self) -> float:
        return self._serialization_time

    @property
    def deserialization_time(self) -> float:
        return self._deserialization_time

    @property
    def bytes_serialized(self) -> int:
        return self._bytes_serialized

    @property
    def bytes_deserialized(self) -> int:
        return self._bytes_deserialized

    # ==========================================================
    # Lifecycle guard
    # ==========================================================

    def _ensure_available(self) -> None:
        if self._closed:
            raise RuntimeError(
                "Serializer service is closed."
            )

    # ==========================================================
    # Codec Lookup
    # ==========================================================

    def codec(
        self,
        format_name: str,
    ) -> BaseCodec:
        self._ensure_available()

        codec = self._registry.get(
            format_name,
        )

        if codec is None:
            raise SerializerNotFoundError(
                f"No serializer registered for "
                f"{format_name}"
            )

        return codec

    def require_codec(
        self,
        format_name: str,
    ) -> BaseCodec:
        return self.codec(
            format_name
        )

    def get_codec(
        self,
        format_name: str,
        default: Any = None,
    ) -> Any:
        self._ensure_available()
        return self._registry.get(
            format_name,
            default,
        )

    # ==========================================================
    # Default Format
    # ==========================================================

    def set_default_format(
        self,
        format_name: str,
    ) -> None:
        self.codec(
            format_name
        )
        self._default_format = str(
            format_name
        )

    def reset_default_format(self) -> None:
        self._default_format = (
            DEFAULT_FORMAT.value
        )

    def resolve_format(
        self,
        format_name: str | None = None,
    ) -> str:
        if format_name:
            return str(
                format_name
            ).strip().lower()

        return self._default_format

    # ==========================================================
    # Serialize
    # ==========================================================

    def serialize(
        self,
        value: Any,
        *,
        format: str | None = None,
        **kwargs: Any,
    ) -> str | bytes:
        self._ensure_available()

        fmt = self.resolve_format(
            format
        )
        codec = self.codec(
            fmt
        )

        start = time.perf_counter()

        try:
            result = codec.serialize(
                value,
                **kwargs,
            )

            duration = (
                time.perf_counter()
                - start
            )

            self._record_serialization(
                fmt,
                duration,
                result,
            )

            return result

        except Exception as exc:
            self._record_failure(
                "serialize",
                fmt,
                start,
                error=exc,
            )
            raise

    # ==========================================================
    # Deserialize
    # ==========================================================

    def deserialize(
        self,
        data: str | bytes,
        *,
        format: str | None = None,
        **kwargs: Any,
    ) -> Any:
        self._ensure_available()

        fmt = self.resolve_format(
            format
        )
        codec = self.codec(
            fmt
        )

        start = time.perf_counter()

        try:
            result = codec.deserialize(
                data,
                **kwargs,
            )

            duration = (
                time.perf_counter()
                - start
            )

            self._record_deserialization(
                fmt,
                duration,
                data,
            )

            return result

        except Exception as exc:
            self._record_failure(
                "deserialize",
                fmt,
                start,
                error=exc,
            )
            raise

    # ==========================================================
    # Request Model
    # ==========================================================

    def serialize_request(
        self,
        request: SerializationRequest,
    ) -> SerializationResponse:
        codec = self.codec(
            request.format,
        )

        method = getattr(
            codec,
            "serialize_request",
            None,
        )

        if callable(method):
            return method(
                request
            )

        data = self.serialize(
            request.value,
            format=request.format,
        )

        return SerializationResponse(
            data=data,
            format=request.format,
            encoding=getattr(
                request,
                "encoding",
                "utf-8",
            ),
            compressed=getattr(
                request,
                "compress",
                False,
            ),
            encrypted=getattr(
                request,
                "encrypt",
                False,
            ),
            metadata={
                "serializer":
                    getattr(
                        codec,
                        "name",
                        request.format,
                    ),
            },
        )

    def deserialize_request(
        self,
        request: DeserializationRequest,
    ) -> DeserializationResponse:
        codec = self.codec(
            request.format,
        )

        method = getattr(
            codec,
            "deserialize_request",
            None,
        )

        if callable(method):
            return method(
                request
            )

        value = self.deserialize(
            request.data,
            format=request.format,
        )

        return DeserializationResponse(
            value=value,
            metadata=getattr(
                request,
                "metadata",
                {},
            ),
            valid=True,
        )

    # ==========================================================
    # Registry
    # ==========================================================

    def supported_formats(
        self,
    ) -> list[str]:
        return self._registry.names()

    def supports(
        self,
        format_name: str,
    ) -> bool:
        try:
            return bool(
                self._registry.contains(
                    format_name,
                )
            )
        except Exception:
            return False

    def capabilities(
        self,
        format_name: str,
    ) -> set[str]:
        method = getattr(
            self._registry,
            "capabilities",
            None,
        )

        if callable(method):
            return set(
                method(
                    format_name
                )
            )

        codec = self.codec(
            format_name
        )

        operations = (
            "serialize",
            "deserialize",
            "serialize_to_file",
            "deserialize_from_file",
            "serialize_to_stream",
            "deserialize_from_stream",
            "serialize_many",
            "deserialize_many",
            "serialize_async",
            "deserialize_async",
            "validate",
        )

        return {
            operation
            for operation in operations
            if callable(
                getattr(
                    codec,
                    operation,
                    None,
                )
            )
        }

    def supports_operation(
        self,
        format_name: str,
        operation: str,
    ) -> bool:
        return (
            operation
            in self.capabilities(
                format_name
            )
        )

    # ==========================================================
    # File Serialization
    # ==========================================================

    def serialize_to_file(
        self,
        value: Any,
        path: str | Path,
        *,
        format: str | None = None,
        **kwargs: Any,
    ) -> Path:
        target = Path(
            path
        )

        fmt = (
            self.detect_format(
                str(target)
            )
            if format is None
            else self.resolve_format(
                format
            )
        )

        codec = self.codec(
            fmt
        )

        method = getattr(
            codec,
            "serialize_to_file",
            None,
        )

        if callable(method):
            try:
                result = method(
                    value,
                    target,
                    **kwargs,
                )
                return (
                    Path(result)
                    if result is not None
                    else target
                )
            except TypeError:
                result = method(
                    value,
                    target,
                )
                return (
                    Path(result)
                    if result is not None
                    else target
                )

        data = self.serialize(
            value,
            format=fmt,
            **kwargs,
        )

        target.parent.mkdir(
            parents=True,
            exist_ok=True,
        )

        if isinstance(
            data,
            bytes,
        ):
            target.write_bytes(
                data
            )
        else:
            target.write_text(
                data,
                encoding="utf-8",
            )

        return target

    # ==========================================================
    # File Deserialization
    # ==========================================================

    def deserialize_from_file(
        self,
        path: str | Path,
        *,
        format: str | None = None,
        **kwargs: Any,
    ) -> Any:
        target = Path(
            path
        )

        fmt = (
            self.detect_format(
                str(target)
            )
            if format is None
            else self.resolve_format(
                format
            )
        )

        codec = self.codec(
            fmt
        )

        method = getattr(
            codec,
            "deserialize_from_file",
            None,
        )

        if callable(method):
            try:
                return method(
                    target,
                    **kwargs,
                )
            except TypeError:
                return method(
                    target
                )

        try:
            data = target.read_text(
                encoding="utf-8"
            )
        except UnicodeDecodeError:
            data = target.read_bytes()

        return self.deserialize(
            data,
            format=fmt,
            **kwargs,
        )

    # ==========================================================
    # Stream Serialization
    # ==========================================================

    def serialize_to_stream(
        self,
        value: Any,
        stream: IO,
        *,
        format: str | None = None,
        **kwargs: Any,
    ) -> None:
        fmt = self.resolve_format(
            format
        )
        codec = self.codec(
            fmt
        )

        method = getattr(
            codec,
            "serialize_to_stream",
            None,
        )

        if callable(method):
            try:
                method(
                    value,
                    stream,
                    **kwargs,
                )
                return
            except TypeError:
                method(
                    value,
                    stream,
                )
                return

        data = self.serialize(
            value,
            format=fmt,
            **kwargs,
        )

        stream.write(
            data
        )

    # ==========================================================
    # Stream Deserialization
    # ==========================================================

    def deserialize_from_stream(
        self,
        stream: IO,
        *,
        format: str | None = None,
        **kwargs: Any,
    ) -> Any:
        fmt = self.resolve_format(
            format
        )
        codec = self.codec(
            fmt
        )

        method = getattr(
            codec,
            "deserialize_from_stream",
            None,
        )

        if callable(method):
            try:
                return method(
                    stream,
                    **kwargs,
                )
            except TypeError:
                return method(
                    stream
                )

        data = stream.read()

        return self.deserialize(
            data,
            format=fmt,
            **kwargs,
        )

    # ==========================================================
    # Batch Serialization
    # ==========================================================

    def serialize_many(
        self,
        objects: Iterable[Any],
        *,
        format: str | None = None,
        **kwargs: Any,
    ) -> list[str | bytes]:
        fmt = self.resolve_format(
            format
        )
        values = list(
            objects
        )
        codec = self.codec(
            fmt
        )

        method = getattr(
            codec,
            "serialize_many",
            None,
        )

        if callable(method):
            try:
                return list(
                    method(
                        values,
                        **kwargs,
                    )
                )
            except TypeError:
                return list(
                    method(values)
                )

        return [
            self.serialize(
                value,
                format=fmt,
                **kwargs,
            )
            for value in values
        ]

    # ==========================================================
    # Batch Deserialization
    # ==========================================================

    def deserialize_many(
        self,
        objects: Iterable[str | bytes],
        *,
        format: str | None = None,
        **kwargs: Any,
    ) -> list[Any]:
        fmt = self.resolve_format(
            format
        )
        values = list(
            objects
        )
        codec = self.codec(
            fmt
        )

        method = getattr(
            codec,
            "deserialize_many",
            None,
        )

        if callable(method):
            try:
                return list(
                    method(
                        values,
                        **kwargs,
                    )
                )
            except TypeError:
                return list(
                    method(values)
                )

        return [
            self.deserialize(
                value,
                format=fmt,
                **kwargs,
            )
            for value in values
        ]

    # ==========================================================
    # Format Detection
    # ==========================================================

    def detect_format(
        self,
        filename: str,
    ) -> str:
        extension = (
            Path(filename)
            .suffix
            .lower()
        )

        mapping = {
            ".json": "json",
            ".yaml": "yaml",
            ".yml": "yaml",
            ".xml": "xml",
            ".toml": "toml",
            ".msgpack": "msgpack",
            ".mpk": "msgpack",
            ".pickle": "pickle",
            ".pkl": "pickle",
            ".csv": "csv",
            ".ini": "ini",
            ".properties": "properties",
            ".env": "dotenv",
        }

        if extension in mapping:
            return mapping[
                extension
            ]

        finder = getattr(
            self._registry,
            "find_by_extension",
            None,
        )

        if callable(finder):
            codec = finder(
                extension
            )

            if codec is not None:
                return getattr(
                    codec,
                    "name",
                    getattr(
                        codec,
                        "format",
                        self._default_format,
                    ),
                )

        return self._default_format

    def detect_from_media_type(
        self,
        media_type: str,
    ) -> str:
        finder = getattr(
            self._registry,
            "find_by_media_type",
            None,
        )

        if callable(finder):
            codec = finder(
                media_type
            )

            if codec is not None:
                return getattr(
                    codec,
                    "name",
                    getattr(
                        codec,
                        "format",
                        self._default_format,
                    ),
                )

        media = str(
            media_type
        ).lower()

        aliases = {
            "application/json":
                "json",
            "text/yaml":
                "yaml",
            "application/yaml":
                "yaml",
            "application/xml":
                "xml",
            "text/xml":
                "xml",
            "text/csv":
                "csv",
            "application/toml":
                "toml",
        }

        if media in aliases:
            return aliases[
                media
            ]

        return self._default_format

    # ==========================================================
    # Automatic Selection
    # ==========================================================

    def choose_format(
        self,
        *,
        format: str | None = None,
        filename: str | Path | None = None,
        media_type: str | None = None,
        value: Any = None,
    ) -> str:
        if format:
            return self.resolve_format(
                format
            )

        if filename is not None:
            detected = self.detect_format(
                str(filename)
            )

            if self.supports(
                detected
            ):
                return detected

        if media_type:
            detected = (
                self.detect_from_media_type(
                    media_type
                )
            )

            if self.supports(
                detected
            ):
                return detected

        if value is not None:
            finder = getattr(
                self._registry,
                "find_for_value",
                None,
            )

            if callable(finder):
                candidates = finder(
                    value
                )

                if candidates:
                    return getattr(
                        candidates[0],
                        "name",
                        getattr(
                            candidates[0],
                            "format",
                            self._default_format,
                        ),
                    )

        return self._default_format

    def serialize_auto(
        self,
        value: Any,
        *,
        format: str | None = None,
        filename: str | Path | None = None,
        media_type: str | None = None,
        **kwargs: Any,
    ) -> str | bytes:
        fmt = self.choose_format(
            format=format,
            filename=filename,
            media_type=media_type,
            value=value,
        )

        return self.serialize(
            value,
            format=fmt,
            **kwargs,
        )

    def deserialize_auto(
        self,
        data: str | bytes,
        *,
        format: str | None = None,
        filename: str | Path | None = None,
        media_type: str | None = None,
        **kwargs: Any,
    ) -> Any:
        fmt = self.choose_format(
            format=format,
            filename=filename,
            media_type=media_type,
        )

        return self.deserialize(
            data,
            format=fmt,
            **kwargs,
        )

    # ==========================================================
    # Validation
    # ==========================================================

    def validate_format(
        self,
        format_name: str,
    ) -> bool:
        return self.supports(
            format_name,
        )

    def validate_value(
        self,
        value: Any,
        *,
        format: str | None = None,
    ) -> bool:
        fmt = self.resolve_format(
            format
        )
        codec = self.codec(
            fmt
        )

        validator = getattr(
            codec,
            "validate",
            None,
        )

        if callable(
            validator
        ):
            try:
                return bool(
                    validator(value)
                )
            except Exception:
                return False

        try:
            self.serialize(
                value,
                format=fmt,
            )
            return True
        except Exception:
            return False

    def validate_data(
        self,
        data: str | bytes,
        *,
        format: str | None = None,
    ) -> bool:
        try:
            self.deserialize(
                data,
                format=format,
            )
            return True
        except Exception:
            return False

    # ==========================================================
    # Size Helpers
    # ==========================================================

    @staticmethod
    def data_size(
        data: Any,
    ) -> int | None:
        if isinstance(
            data,
            bytes,
        ):
            return len(data)

        if isinstance(
            data,
            str,
        ):
            return len(
                data.encode(
                    "utf-8"
                )
            )

        try:
            return len(data)
        except Exception:
            return None

    def serialized_size(
        self,
        value: Any,
        *,
        format: str | None = None,
        **kwargs: Any,
    ) -> int | None:
        codec = self.codec(
            self.resolve_format(
                format
            )
        )

        method = getattr(
            codec,
            "serialized_size",
            None,
        )

        if callable(method):
            try:
                return int(
                    method(
                        value,
                        **kwargs,
                    )
                )
            except Exception:
                pass

        return self.data_size(
            self.serialize(
                value,
                format=format,
                **kwargs,
            )
        )

    # ==========================================================
    # Hash / Fingerprint
    # ==========================================================

    def fingerprint(
        self,
        value: Any,
        *,
        format: str | None = None,
    ) -> str:
        data = self.serialize(
            value,
            format=format,
        )

        if isinstance(
            data,
            str,
        ):
            data = data.encode(
                "utf-8"
            )

        return hashlib.sha256(
            data
        ).hexdigest()

    # ==========================================================
    # Fallback
    # ==========================================================

    def serialize_with_fallback(
        self,
        value: Any,
        formats: Sequence[str],
        **kwargs: Any,
    ) -> tuple[str, str | bytes]:
        errors: list[str] = []

        for fmt in formats:
            try:
                return (
                    fmt,
                    self.serialize(
                        value,
                        format=fmt,
                        **kwargs,
                    ),
                )
            except Exception as exc:
                errors.append(
                    f"{fmt}: {exc}"
                )

        raise SerializerNotFoundError(
            "All serializer fallbacks failed: "
            + "; ".join(errors)
        )

    def deserialize_with_fallback(
        self,
        data: str | bytes,
        formats: Sequence[str],
        **kwargs: Any,
    ) -> tuple[str, Any]:
        errors: list[str] = []

        for fmt in formats:
            try:
                return (
                    fmt,
                    self.deserialize(
                        data,
                        format=fmt,
                        **kwargs,
                    ),
                )
            except Exception as exc:
                errors.append(
                    f"{fmt}: {exc}"
                )

        raise SerializerNotFoundError(
            "All deserializer fallbacks failed: "
            + "; ".join(errors)
        )

    # ==========================================================
    # Async API
    # ==========================================================

    async def serialize_async(
        self,
        value: Any,
        *,
        format: str | None = None,
        **kwargs: Any,
    ) -> str | bytes:
        fmt = self.resolve_format(
            format
        )
        codec = self.codec(
            fmt
        )

        method = getattr(
            codec,
            "serialize_async",
            None,
        )

        if callable(method):
            return await method(
                value,
                **kwargs,
            )

        return await asyncio.to_thread(
            self.serialize,
            value,
            format=fmt,
            **kwargs,
        )

    async def deserialize_async(
        self,
        data: str | bytes,
        *,
        format: str | None = None,
        **kwargs: Any,
    ) -> Any:
        fmt = self.resolve_format(
            format
        )
        codec = self.codec(
            fmt
        )

        method = getattr(
            codec,
            "deserialize_async",
            None,
        )

        if callable(method):
            return await method(
                data,
                **kwargs,
            )

        return await asyncio.to_thread(
            self.deserialize,
            data,
            format=fmt,
            **kwargs,
        )

    async def serialize_many_async(
        self,
        objects: Iterable[Any],
        *,
        format: str | None = None,
        **kwargs: Any,
    ) -> list[str | bytes]:
        values = list(
            objects
        )

        return await asyncio.to_thread(
            self.serialize_many,
            values,
            format=format,
            **kwargs,
        )

    async def deserialize_many_async(
        self,
        objects: Iterable[str | bytes],
        *,
        format: str | None = None,
        **kwargs: Any,
    ) -> list[Any]:
        values = list(
            objects
        )

        return await asyncio.to_thread(
            self.deserialize_many,
            values,
            format=format,
            **kwargs,
        )

    # ==========================================================
    # Metrics
    # ==========================================================

    def _record_serialization(
        self,
        fmt: str,
        duration: float,
        result: Any,
    ) -> None:
        size = self.data_size(
            result
        )

        with self._lock:
            self._serialization_count += 1
            self._serialization_time += duration

            if size is not None:
                self._bytes_serialized += size

            self._append_history(
                SerializationOperation(
                    operation="serialize",
                    format=fmt,
                    duration=duration,
                    output_size=size,
                )
            )

    def _record_deserialization(
        self,
        fmt: str,
        duration: float,
        data: Any,
    ) -> None:
        size = self.data_size(
            data
        )

        with self._lock:
            self._deserialization_count += 1
            self._deserialization_time += duration

            if size is not None:
                self._bytes_deserialized += size

            self._append_history(
                SerializationOperation(
                    operation="deserialize",
                    format=fmt,
                    duration=duration,
                    input_size=size,
                )
            )

    def _record_failure(
        self,
        operation: str,
        fmt: str,
        start: float,
        *,
        error: Exception,
    ) -> None:
        duration = (
            time.perf_counter()
            - start
        )

        with self._lock:
            self._failures += 1
            self._append_history(
                SerializationOperation(
                    operation=operation,
                    format=fmt,
                    duration=duration,
                    success=False,
                    error=str(error),
                )
            )

    def _append_history(
        self,
        operation: SerializationOperation,
    ) -> None:
        self._history.append(
            operation
        )

        if (
            len(self._history)
            > self._history_limit
        ):
            del self._history[
                : len(self._history)
                - self._history_limit
            ]

    def reset_metrics(self) -> None:
        with self._lock:
            self._serialization_count = 0
            self._deserialization_count = 0
            self._serialization_time = 0.0
            self._deserialization_time = 0.0
            self._bytes_serialized = 0
            self._bytes_deserialized = 0
            self._failures = 0
            self._history.clear()

    def statistics(
        self,
    ) -> dict[str, Any]:
        with self._lock:
            serialization_average = (
                self._serialization_time
                / self._serialization_count
                if self._serialization_count
                else 0.0
            )

            deserialization_average = (
                self._deserialization_time
                / self._deserialization_count
                if self._deserialization_count
                else 0.0
            )

            return {
                "default_format":
                    self._default_format,
                "serialization_count":
                    self._serialization_count,
                "deserialization_count":
                    self._deserialization_count,
                "serialization_time":
                    self._serialization_time,
                "deserialization_time":
                    self._deserialization_time,
                "average_serialization_time":
                    serialization_average,
                "average_deserialization_time":
                    deserialization_average,
                "bytes_serialized":
                    self._bytes_serialized,
                "bytes_deserialized":
                    self._bytes_deserialized,
                "failures":
                    self._failures,
                "history_size":
                    len(self._history),
                "initialized":
                    self._initialized,
                "closed":
                    self._closed,
            }

    def history(
        self,
        *,
        limit: int | None = None,
    ) -> list[SerializationOperation]:
        with self._lock:
            values = list(
                self._history
            )

        if limit is None:
            return values

        return values[
            -max(0, int(limit)):
        ]

    # ==========================================================
    # Diagnostics
    # ==========================================================

    def diagnostics(
        self,
    ) -> dict[str, Any]:
        formats = self.supported_formats()

        return {
            "service":
                "Serializer",
            "default_format":
                self._default_format,
            "formats":
                formats,
            "format_count":
                len(formats),
            "statistics":
                self.statistics(),
            "health":
                self.health(),
        }

    def health(
        self,
    ) -> bool:
        if self._closed:
            return False

        registry_health = getattr(
            self._registry,
            "health",
            None,
        )

        if callable(
            registry_health
        ):
            try:
                return bool(
                    registry_health()
                )
            except Exception:
                return False

        return True

    # ==========================================================
    # Self Test
    # ==========================================================

    def self_test(
        self,
        *,
        formats: Sequence[str] | None = None,
    ) -> bool:
        sample = {
            "framework": "AURA",
            "version": 1,
        }

        selected = (
            list(formats)
            if formats is not None
            else self.supported_formats()
        )

        for fmt in selected:
            try:
                data = self.serialize(
                    sample,
                    format=fmt,
                )

                obj = self.deserialize(
                    data,
                    format=fmt,
                )

                if obj != sample:
                    return False

            except Exception:
                return False

        return True

    def self_test_report(
        self,
        *,
        formats: Sequence[str] | None = None,
    ) -> dict[str, Any]:
        sample = {
            "framework": "AURA",
            "version": 1,
        }

        selected = (
            list(formats)
            if formats is not None
            else self.supported_formats()
        )

        report: dict[
            str,
            dict[str, Any],
        ] = {}

        for fmt in selected:
            start = time.perf_counter()

            try:
                data = self.serialize(
                    sample,
                    format=fmt,
                )
                obj = self.deserialize(
                    data,
                    format=fmt,
                )

                report[fmt] = {
                    "passed":
                        obj == sample,
                    "duration":
                        time.perf_counter()
                        - start,
                }

            except Exception as exc:
                report[fmt] = {
                    "passed":
                        False,
                    "duration":
                        time.perf_counter()
                        - start,
                    "error":
                        str(exc),
                }

        return report

    # ==========================================================
    # Codec Lifecycle
    # ==========================================================

    def initialize(self) -> None:
        if self._initialized:
            return

        initialize = getattr(
            self._registry,
            "initialize",
            None,
        )

        if callable(initialize):
            initialize()

        self._initialized = True
        self._closed = False

    def reset(self) -> None:
        reset = getattr(
            self._registry,
            "reset",
            None,
        )

        if callable(reset):
            reset()

        self.reset_metrics()

    def shutdown(self) -> None:
        if self._closed:
            return

        shutdown = getattr(
            self._registry,
            "shutdown",
            None,
        )

        if callable(shutdown):
            shutdown()

        self._closed = True
        self._initialized = False

    def reopen(self) -> None:
        reopen = getattr(
            self._registry,
            "reopen",
            None,
        )

        if callable(reopen):
            reopen()

        self._closed = False

    # ==========================================================
    # Registration Convenience
    # ==========================================================

    def register(
        self,
        codec: Any,
        *,
        name: str | None = None,
        aliases: Iterable[str] = (),
        replace: bool = False,
        **kwargs: Any,
    ) -> Any:
        register = getattr(
            self._registry,
            "register",
        )

        return register(
            codec,
            name=name,
            aliases=aliases,
            replace=replace,
            **kwargs,
        )

    def unregister(
        self,
        format_name: str,
    ) -> Any:
        unregister = getattr(
            self._registry,
            "unregister",
        )

        return unregister(
            format_name
        )

    # ==========================================================
    # Configuration
    # ==========================================================

    def configuration(
        self,
    ) -> dict[str, Any]:
        return {
            "default_format":
                self._default_format,
            "history_limit":
                self._history_limit,
        }

    def configure(
        self,
        options: Mapping[str, Any],
    ) -> None:
        if "default_format" in options:
            self.set_default_format(
                str(
                    options[
                        "default_format"
                    ]
                )
            )

        if "history_limit" in options:
            value = int(
                options[
                    "history_limit"
                ]
            )

            if value < 0:
                raise ValueError(
                    "history_limit cannot be negative."
                )

            self._history_limit = value

    # ==========================================================
    # Context Management
    # ==========================================================

    def __enter__(
        self,
    ) -> "Serializer":
        self.initialize()
        return self

    def __exit__(
        self,
        exc_type: Any,
        exc_value: Any,
        traceback: Any,
    ) -> bool:
        self.shutdown()
        return False

    def __repr__(
        self,
    ) -> str:
        return (
            f"Serializer("
            f"default_format="
            f"{self._default_format!r}, "
            f"formats="
            f"{len(self.supported_formats())}, "
            f"closed="
            f"{self._closed})"
        )


# ==========================================================
# Specialized service views
# ==========================================================

class DeserializerService(Serializer):
    """Service view focused on deserialization operations."""

    def serialize(
        self,
        value: Any,
        *,
        format: str | None = None,
        **kwargs: Any,
    ) -> str | bytes:
        raise NotImplementedError(
            "DeserializerService does not expose serialize()."
        )


class SerializerService(Serializer):
    """Explicit serializer service alias for dependency injection."""

    pass


# ==========================================================
# Factory helper
# ==========================================================

def create_serializer(
    registry: Any = None,
    *,
    default_format: str | None = None,
) -> Serializer:
    """Create an independent high-level serialization service."""
    return Serializer(
        registry=registry,
        default_format=default_format,
    )


# ==========================================================
# Default Serializer
# ==========================================================

serializer = Serializer()

__all__ = [
    "SerializationOperation",
    "Serializer",
    "SerializerService",
    "DeserializerService",
    "create_serializer",
    "serializer",
]