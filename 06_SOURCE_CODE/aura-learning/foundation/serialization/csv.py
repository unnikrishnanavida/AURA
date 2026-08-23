"""
==============================================================
AURA Framework

CSV Serializer

Enterprise CSV Serialization

Responsibilities
----------------
• CSV Serialization / Deserialization
• File and Stream Support
• Batch Operations
• Async APIs
• Compression
• Metrics and Performance
• Cache
• Thread Safety
• Registry Integration
• Diagnostics and Health
• Lifecycle Management
• Dialect and Formatting Controls
• Header / Schema Validation
• Row Filtering and Projection
• CSVL / Record-Oriented Helpers
==============================================================
"""

from __future__ import annotations

import asyncio
import csv
import gzip
import io
import json
import threading
import time

from collections import OrderedDict
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any, Callable, IO, Iterable, Iterator, Mapping, Sequence

try:
    from .interfaces import BaseCodec
except ImportError:
    class BaseCodec:
        pass

try:
    from .models import (
        SerializationRequest,
        SerializationResponse,
        DeserializationRequest,
        DeserializationResponse,
    )
except ImportError:
    SerializationRequest = Any
    SerializationResponse = Any
    DeserializationRequest = Any
    DeserializationResponse = Any

try:
    from .constants import SerializationFormat
except ImportError:
    class SerializationFormat:
        CSV = "csv"

try:
    from .exceptions import SerializationError, DeserializationError
except ImportError:
    class SerializationError(Exception):
        pass
    class DeserializationError(Exception):
        pass

try:
    from .utilities import current_iso_timestamp
except ImportError:
    def current_iso_timestamp() -> str:
        return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())

try:
    from .version import VERSION, __version__
except ImportError:
    VERSION = "1.0.0"
    __version__ = VERSION


class CsvCodec(BaseCodec):
    """
    Enterprise CSV codec.

    CSV is fundamentally tabular, so the canonical Python representation
    used by this codec is:

        list[dict[str, Any]]

    A sequence of mappings is also accepted for serialization.  A single
    mapping can be serialized as one row when explicit fieldnames are
    supplied.
    """

    DEFAULT_DELIMITER = ","
    DEFAULT_QUOTECHAR = '"'
    DEFAULT_ESCAPECHAR = None
    DEFAULT_LINETERMINATOR = "\n"
    DEFAULT_QUOTING = csv.QUOTE_MINIMAL
    DEFAULT_ENCODING = "utf-8"
    DEFAULT_CACHE_SIZE = 256
    DEFAULT_FIELDNAMES = None

    def __init__(
        self,
        *,
        delimiter: str = DEFAULT_DELIMITER,
        quotechar: str = DEFAULT_QUOTECHAR,
        escapechar: str | None = DEFAULT_ESCAPECHAR,
        lineterminator: str = DEFAULT_LINETERMINATOR,
        quoting: int = DEFAULT_QUOTING,
        skipinitialspace: bool = False,
        strict: bool = False,
        doublequote: bool = True,
        encoding: str = DEFAULT_ENCODING,
        cache_size: int = DEFAULT_CACHE_SIZE,
    ) -> None:
        self._delimiter = delimiter
        self._quotechar = quotechar
        self._escapechar = escapechar
        self._lineterminator = lineterminator
        self._quoting = quoting
        self._skipinitialspace = skipinitialspace
        self._strict = strict
        self._doublequote = doublequote
        self._encoding = encoding
        self._cache_size = max(0, int(cache_size))

        self._serialization_count = 0
        self._deserialization_count = 0
        self._serialization_time = 0.0
        self._deserialization_time = 0.0
        self._cache_hits = 0
        self._cache_misses = 0
        self._rows_serialized = 0
        self._rows_deserialized = 0

        self._lock = threading.RLock()
        self._cache: OrderedDict[str, str] = OrderedDict()

    # ======================================================
    # Identity
    # ======================================================

    @property
    def name(self) -> str:
        return "csv"

    @property
    def format(self) -> str:
        value = getattr(SerializationFormat, "CSV", "csv")
        return getattr(value, "value", value)

    @property
    def encoding(self) -> str:
        return self._encoding

    @property
    def delimiter(self) -> str:
        return self._delimiter

    @property
    def quotechar(self) -> str:
        return self._quotechar

    @property
    def escapechar(self) -> str | None:
        return self._escapechar

    @property
    def lineterminator(self) -> str:
        return self._lineterminator

    @property
    def quoting(self) -> int:
        return self._quoting

    @property
    def cache_size(self) -> int:
        return self._cache_size

    # ======================================================
    # Configuration
    # ======================================================

    def configuration(self) -> dict[str, Any]:
        return {
            "delimiter": self._delimiter,
            "quotechar": self._quotechar,
            "escapechar": self._escapechar,
            "lineterminator": self._lineterminator,
            "quoting": self._quoting,
            "skipinitialspace": self._skipinitialspace,
            "strict": self._strict,
            "doublequote": self._doublequote,
            "encoding": self._encoding,
            "cache_size": self._cache_size,
        }

    def set_delimiter(self, delimiter: str) -> None:
        self._validate_delimiter(delimiter)
        self._delimiter = delimiter
        self.clear_cache()

    def set_quotechar(self, quotechar: str) -> None:
        self._validate_quotechar(quotechar)
        self._quotechar = quotechar
        self.clear_cache()

    def set_escapechar(self, escapechar: str | None) -> None:
        if escapechar is not None:
            self._validate_escapechar(escapechar)
        self._escapechar = escapechar
        self.clear_cache()

    def set_encoding(self, encoding: str) -> None:
        "Set text encoding used by file operations."
        "The codec does not silently transcode arbitrary byte payloads."
        "A lookup is performed so configuration errors fail early."
        "".encode(encoding)
        self._encoding = encoding

    def set_cache_size(self, size: int) -> None:
        if size < 0:
            raise ValueError("cache size cannot be negative")
        with self._lock:
            self._cache_size = int(size)
            while len(self._cache) > self._cache_size:
                self._cache.popitem(last=False)

    # ======================================================
    # Configuration Validation
    # ======================================================

    @staticmethod
    def _validate_delimiter(delimiter: str) -> None:
        if not isinstance(delimiter, str) or len(delimiter) != 1:
            raise ValueError("CSV delimiter must be exactly one character")

    @staticmethod
    def _validate_quotechar(quotechar: str) -> None:
        if not isinstance(quotechar, str) or len(quotechar) != 1:
            raise ValueError("CSV quotechar must be exactly one character")

    @staticmethod
    def _validate_escapechar(escapechar: str) -> None:
        if not isinstance(escapechar, str) or len(escapechar) != 1:
            raise ValueError("CSV escapechar must be exactly one character")

    # ======================================================
    # Normalization
    # ======================================================

    @staticmethod
    def _normalize_value(value: Any) -> Any:
        if is_dataclass(value) and not isinstance(value, type):
            return asdict(value)

        if isinstance(value, Mapping):
            return dict(value)

        if isinstance(value, (list, tuple)):
            return list(value)

        return value

    def _normalize_rows(
        self,
        value: Any,
        *,
        fieldnames: Sequence[str] | None = None,
    ) -> list[dict[str, Any]]:
        value = self._normalize_value(value)

        if isinstance(value, Mapping):
            if fieldnames is None:
                return [dict(value)]
            return [dict(value)]

        if isinstance(value, (str, bytes, bytearray)):
            raise SerializationError(
                "CSV input must be a sequence of rows, not a string or bytes."
            )

        try:
            rows = list(value)
        except TypeError as exc:
            raise SerializationError(
                "CSV serialization requires an iterable of row mappings."
            ) from exc

        normalized: list[dict[str, Any]] = []

        for index, row in enumerate(rows):
            row = self._normalize_value(row)

            if not isinstance(row, Mapping):
                if fieldnames is not None and isinstance(row, Sequence):
                    row = dict(zip(fieldnames, row))
                else:
                    raise SerializationError(
                        f"CSV row {index} must be a mapping."
                    )

            normalized.append(dict(row))

        return normalized

    # ======================================================
    # Fieldnames
    # ======================================================

    @staticmethod
    def infer_fieldnames(rows: Sequence[Mapping[str, Any]]) -> list[str]:
        names: list[str] = []
        seen: set[str] = set()

        for row in rows:
            for key in row.keys():
                name = str(key)
                if name not in seen:
                    seen.add(name)
                    names.append(name)

        return names

    def resolve_fieldnames(
        self,
        rows: Sequence[Mapping[str, Any]],
        fieldnames: Sequence[str] | None = None,
    ) -> list[str]:
        if fieldnames is not None:
            result = [str(item) for item in fieldnames]
            if len(result) != len(set(result)):
                raise SerializationError("CSV fieldnames must be unique.")
            return result

        return self.infer_fieldnames(rows)

    # ======================================================
    # Core Serialization
    # ======================================================

    def serialize(
        self,
        value: Any,
        *,
        context: Any = None,
        fieldnames: Sequence[str] | None = None,
        include_header: bool = True,
    ) -> str:
        start = time.perf_counter()

        try:
            rows = self._normalize_rows(value, fieldnames=fieldnames)
            names = self.resolve_fieldnames(rows, fieldnames)

            output = io.StringIO(newline="")
            writer = csv.DictWriter(
                output,
                fieldnames=names,
                delimiter=self._delimiter,
                quotechar=self._quotechar,
                escapechar=self._escapechar,
                lineterminator=self._lineterminator,
                quoting=self._quoting,
                skipinitialspace=self._skipinitialspace,
                strict=self._strict,
                doublequote=self._doublequote,
                extrasaction="ignore",
            )

            if include_header:
                writer.writeheader()

            for row in rows:
                writer.writerow({
                    name: row.get(name, "")
                    for name in names
                })

            result = output.getvalue()
            self._rows_serialized += len(rows)
            return result

        except SerializationError:
            raise
        except Exception as exc:
            raise SerializationError(str(exc)) from exc
        finally:
            self._serialization_count += 1
            self._serialization_time += time.perf_counter() - start

    # ======================================================
    # Core Deserialization
    # ======================================================

    def deserialize(
        self,
        data: str | bytes,
        *,
        context: Any = None,
        fieldnames: Sequence[str] | None = None,
        has_header: bool = True,
    ) -> list[dict[str, Any]]:
        start = time.perf_counter()

        try:
            if isinstance(data, bytes):
                data = data.decode(self._encoding)

            if not isinstance(data, str):
                raise DeserializationError(
                    "CSV data must be str or bytes."
                )

            stream = io.StringIO(data, newline="")
            if has_header:
                reader = csv.DictReader(
                    stream,
                    delimiter=self._delimiter,
                    quotechar=self._quotechar,
                    escapechar=self._escapechar,
                    skipinitialspace=self._skipinitialspace,
                    strict=self._strict,
                    doublequote=self._doublequote,
                )
                rows = [dict(row) for row in reader]
            else:
                if fieldnames is None:
                    raise DeserializationError(
                        "fieldnames are required when has_header=False."
                    )
                reader = csv.reader(
                    stream,
                    delimiter=self._delimiter,
                    quotechar=self._quotechar,
                    escapechar=self._escapechar,
                    skipinitialspace=self._skipinitialspace,
                    strict=self._strict,
                    doublequote=self._doublequote,
                )
                rows = [
                    dict(zip(fieldnames, row))
                    for row in reader
                ]

            self._rows_deserialized += len(rows)
            return rows

        except DeserializationError:
            raise
        except Exception as exc:
            raise DeserializationError(str(exc)) from exc
        finally:
            self._deserialization_count += 1
            self._deserialization_time += time.perf_counter() - start

    # ======================================================
    # Request / Response API
    # ======================================================

    def serialize_request(
        self,
        request: SerializationRequest,
    ) -> SerializationResponse:
        data = self.serialize(request.value)

        return SerializationResponse(
            data=data,
            format=self.format,
            encoding=getattr(request, "encoding", self._encoding),
            compressed=getattr(request, "compress", False),
            encrypted=getattr(request, "encrypt", False),
            metadata={
                "serializer": self.name,
                "timestamp": current_iso_timestamp(),
                "rows": self._count_serialized_rows(data),
            },
        )

    def deserialize_request(
        self,
        request: DeserializationRequest,
    ) -> DeserializationResponse:
        value = self.deserialize(request.data)

        return DeserializationResponse(
            value=value,
            metadata=getattr(request, "metadata", {}),
            valid=True,
        )

    # ======================================================
    # Row Counting
    # ======================================================

    def _count_serialized_rows(self, data: str) -> int:
        if not data.strip():
            return 0
        try:
            return max(0, sum(1 for _ in csv.reader(
                io.StringIO(data),
                delimiter=self._delimiter,
                quotechar=self._quotechar,
            )) - 1)
        except Exception:
            return 0

    def count_rows(
        self,
        data: str | bytes,
        *,
        has_header: bool = True,
    ) -> int:
        rows = self.deserialize(
            data,
            has_header=has_header,
            fieldnames=[] if not has_header else None,
        ) if has_header else self._deserialize_without_count(
            data,
            fieldnames=[],
        )
        return len(rows)

    def _deserialize_without_count(
        self,
        data: str | bytes,
        *,
        fieldnames: Sequence[str],
    ) -> list[dict[str, Any]]:
        if isinstance(data, bytes):
            data = data.decode(self._encoding)

        reader = csv.reader(
            io.StringIO(data, newline=""),
            delimiter=self._delimiter,
            quotechar=self._quotechar,
            escapechar=self._escapechar,
            skipinitialspace=self._skipinitialspace,
            strict=self._strict,
            doublequote=self._doublequote,
        )
        return [dict(zip(fieldnames, row)) for row in reader]

    # ======================================================
    # Type Support
    # ======================================================

    def supports(self, value: type) -> bool:
        return value in (
            dict,
            list,
            tuple,
        )

    def validate(self, value: Any) -> bool:
        try:
            self.serialize(value)
            return True
        except Exception:
            return False

    # ======================================================
    # Header Validation
    # ======================================================

    @staticmethod
    def validate_fieldnames(
        fieldnames: Sequence[str],
    ) -> bool:
        try:
            values = [str(item) for item in fieldnames]
            return (
                bool(values)
                and len(values) == len(set(values))
                and all(bool(value) for value in values)
            )
        except Exception:
            return False

    def validate_headers(
        self,
        data: str | bytes,
        expected: Sequence[str],
    ) -> bool:
        if isinstance(data, bytes):
            data = data.decode(self._encoding)

        reader = csv.reader(
            io.StringIO(data, newline=""),
            delimiter=self._delimiter,
            quotechar=self._quotechar,
            escapechar=self._escapechar,
        )

        try:
            actual = next(reader)
        except StopIteration:
            return False

        return actual == [str(item) for item in expected]

    # ======================================================
    # Schema Validation
    # ======================================================

    def validate_schema(
        self,
        rows: Sequence[Mapping[str, Any]],
        required_fields: Sequence[str],
    ) -> bool:
        required = {str(item) for item in required_fields}

        for row in rows:
            if not required.issubset({str(key) for key in row.keys()}):
                return False

        return True

    def project_columns(
        self,
        rows: Iterable[Mapping[str, Any]],
        columns: Sequence[str],
    ) -> list[dict[str, Any]]:
        names = [str(column) for column in columns]
        return [
            {name: row.get(name, "") for name in names}
            for row in rows
        ]

    # ======================================================
    # Row Filtering
    # ======================================================

    def filter_rows(
        self,
        rows: Iterable[Mapping[str, Any]],
        predicate: Callable[[Mapping[str, Any]], bool],
    ) -> list[dict[str, Any]]:
        return [
            dict(row)
            for row in rows
            if predicate(row)
        ]

    def sort_rows(
        self,
        rows: Iterable[Mapping[str, Any]],
        key: str,
        *,
        reverse: bool = False,
    ) -> list[dict[str, Any]]:
        return sorted(
            (dict(row) for row in rows),
            key=lambda row: row.get(key, ""),
            reverse=reverse,
        )

    # ======================================================
    # File API
    # ======================================================

    def serialize_to_file(
        self,
        value: Any,
        path: str | Path,
        *,
        fieldnames: Sequence[str] | None = None,
        include_header: bool = True,
    ) -> Path:
        path = Path(path)
        path.write_text(
            self.serialize(
                value,
                fieldnames=fieldnames,
                include_header=include_header,
            ),
            encoding=self._encoding,
            newline="",
        )
        return path

    def deserialize_from_file(
        self,
        path: str | Path,
        *,
        fieldnames: Sequence[str] | None = None,
        has_header: bool = True,
    ) -> list[dict[str, Any]]:
        path = Path(path)
        return self.deserialize(
            path.read_text(
                encoding=self._encoding,
            ),
            fieldnames=fieldnames,
            has_header=has_header,
        )

    # ======================================================
    # Stream API
    # ======================================================

    def serialize_to_stream(
        self,
        value: Any,
        stream: IO[str],
        *,
        fieldnames: Sequence[str] | None = None,
        include_header: bool = True,
    ) -> None:
        stream.write(
            self.serialize(
                value,
                fieldnames=fieldnames,
                include_header=include_header,
            )
        )

    def deserialize_from_stream(
        self,
        stream: IO[str],
        *,
        fieldnames: Sequence[str] | None = None,
        has_header: bool = True,
    ) -> list[dict[str, Any]]:
        return self.deserialize(
            stream.read(),
            fieldnames=fieldnames,
            has_header=has_header,
        )

    # ======================================================
    # Batch API
    # ======================================================

    def serialize_many(
        self,
        objects: Iterable[Any],
        *,
        fieldnames: Sequence[str] | None = None,
    ) -> list[str]:
        return [
            self.serialize(obj, fieldnames=fieldnames)
            for obj in objects
        ]

    def deserialize_many(
        self,
        objects: Iterable[str | bytes],
        *,
        has_header: bool = True,
    ) -> list[list[dict[str, Any]]]:
        return [
            self.deserialize(obj, has_header=has_header)
            for obj in objects
        ]

    # ======================================================
    # Record-Oriented API
    # ======================================================

    def serialize_record(
        self,
        record: Mapping[str, Any],
        *,
        fieldnames: Sequence[str] | None = None,
        include_header: bool = True,
    ) -> str:
        return self.serialize(
            [dict(record)],
            fieldnames=fieldnames,
            include_header=include_header,
        )

    def deserialize_first_record(
        self,
        data: str | bytes,
    ) -> dict[str, Any] | None:
        rows = self.deserialize(data)
        return rows[0] if rows else None

    # ======================================================
    # Compression
    # ======================================================

    def serialize_compressed(
        self,
        value: Any,
        *,
        fieldnames: Sequence[str] | None = None,
    ) -> bytes:
        text = self.serialize(
            value,
            fieldnames=fieldnames,
        )
        return gzip.compress(
            text.encode(self._encoding)
        )

    def deserialize_compressed(
        self,
        data: bytes,
        *,
        has_header: bool = True,
    ) -> list[dict[str, Any]]:
        try:
            text = gzip.decompress(data).decode(self._encoding)
            return self.deserialize(
                text,
                has_header=has_header,
            )
        except Exception as exc:
            raise DeserializationError(str(exc)) from exc

    # ======================================================
    # Async API
    # ======================================================

    async def serialize_async(
        self,
        value: Any,
        *,
        fieldnames: Sequence[str] | None = None,
    ) -> str:
        return await asyncio.to_thread(
            self.serialize,
            value,
            fieldnames=fieldnames,
        )

    async def deserialize_async(
        self,
        data: str | bytes,
        *,
        has_header: bool = True,
    ) -> list[dict[str, Any]]:
        return await asyncio.to_thread(
            self.deserialize,
            data,
            has_header=has_header,
        )

    async def serialize_to_file_async(
        self,
        value: Any,
        path: str | Path,
        *,
        fieldnames: Sequence[str] | None = None,
    ) -> Path:
        return await asyncio.to_thread(
            self.serialize_to_file,
            value,
            path,
            fieldnames=fieldnames,
        )

    async def deserialize_from_file_async(
        self,
        path: str | Path,
        *,
        has_header: bool = True,
    ) -> list[dict[str, Any]]:
        return await asyncio.to_thread(
            self.deserialize_from_file,
            path,
            has_header=has_header,
        )

    # ======================================================
    # Metrics
    # ======================================================

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
    def average_serialization_time(self) -> float:
        if self._serialization_count == 0:
            return 0.0
        return (
            self._serialization_time
            / self._serialization_count
        )

    @property
    def average_deserialization_time(self) -> float:
        if self._deserialization_count == 0:
            return 0.0
        return (
            self._deserialization_time
            / self._deserialization_count
        )

    @property
    def cache_hits(self) -> int:
        return self._cache_hits

    @property
    def cache_misses(self) -> int:
        return self._cache_misses

    @property
    def rows_serialized(self) -> int:
        return self._rows_serialized

    @property
    def rows_deserialized(self) -> int:
        return self._rows_deserialized

    def serialize_with_metrics(
        self,
        value: Any,
        *,
        fieldnames: Sequence[str] | None = None,
    ) -> str:
        return self.serialize(
            value,
            fieldnames=fieldnames,
        )

    def deserialize_with_metrics(
        self,
        data: str | bytes,
        *,
        has_header: bool = True,
    ) -> list[dict[str, Any]]:
        return self.deserialize(
            data,
            has_header=has_header,
        )

    def statistics(self) -> dict[str, Any]:
        return {
            "serialized": self.serialization_count,
            "deserialized": self.deserialization_count,
            "serialization_time": self.serialization_time,
            "deserialization_time": self.deserialization_time,
            "average_serialization_time":
                self.average_serialization_time,
            "average_deserialization_time":
                self.average_deserialization_time,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "rows_serialized": self.rows_serialized,
            "rows_deserialized": self.rows_deserialized,
        }

    def performance(self) -> dict[str, Any]:
        return {
            "operations":
                self.serialization_count
                + self.deserialization_count,
            "serialization_rate":
                self._rate(
                    self.serialization_count,
                    self.serialization_time,
                ),
            "deserialization_rate":
                self._rate(
                    self.deserialization_count,
                    self.deserialization_time,
                ),
            "average_serialization_time":
                self.average_serialization_time,
            "average_deserialization_time":
                self.average_deserialization_time,
        }

    @staticmethod
    def _rate(count: int, duration: float) -> float:
        if duration <= 0:
            return 0.0
        return count / duration

    def reset_metrics(self) -> None:
        self._serialization_count = 0
        self._deserialization_count = 0
        self._serialization_time = 0.0
        self._deserialization_time = 0.0
        self._rows_serialized = 0
        self._rows_deserialized = 0

    # ======================================================
    # Cache
    # ======================================================

    def _cache_key(
        self,
        value: Any,
        fieldnames: Sequence[str] | None,
    ) -> str:
        try:
            payload = {
                "value": value,
                "fieldnames": list(fieldnames)
                if fieldnames is not None
                else None,
                "configuration": self.configuration(),
            }
            return json.dumps(
                payload,
                sort_keys=True,
                default=str,
                ensure_ascii=False,
            )
        except Exception:
            return repr(
                (value, fieldnames, self.configuration())
            )

    def clear_cache(self) -> None:
        with self._lock:
            self._cache.clear()

    def cache_entries(self) -> int:
        with self._lock:
            return len(self._cache)

    def serialize_cached(
        self,
        value: Any,
        *,
        fieldnames: Sequence[str] | None = None,
    ) -> str:
        if self._cache_size == 0:
            return self.serialize(
                value,
                fieldnames=fieldnames,
            )

        key = self._cache_key(value, fieldnames)

        with self._lock:
            if key in self._cache:
                self._cache_hits += 1
                self._cache.move_to_end(key)
                return self._cache[key]

            self._cache_misses += 1

        result = self.serialize(
            value,
            fieldnames=fieldnames,
        )

        with self._lock:
            self._cache[key] = result
            self._cache.move_to_end(key)

            while len(self._cache) > self._cache_size:
                self._cache.popitem(last=False)

        return result

    # ======================================================
    # Runtime Information
    # ======================================================

    def runtime_information(self) -> dict[str, Any]:
        return {
            "codec": self.name,
            "format": self.format,
            "version": VERSION,
            "encoding": self.encoding,
            "configuration": self.configuration(),
            "statistics": self.statistics(),
        }

    def runtime_summary(self) -> dict[str, Any]:
        return {
            "codec": self.name,
            "format": self.format,
            "version": VERSION,
            "healthy": self.health(),
            "cache_entries": self.cache_entries(),
            "statistics": self.statistics(),
        }

    # ======================================================
    # Registry
    # ======================================================

    def register(self, registry: Any) -> None:
        registry.register(self)

    def unregister(self, registry: Any) -> None:
        registry.unregister(self.name)

    # ======================================================
    # Diagnostics
    # ======================================================

    def diagnostics(self) -> dict[str, Any]:
        return {
            "healthy": self.health(),
            "runtime": self.runtime_information(),
            "performance": self.performance(),
            "cache_entries": self.cache_entries(),
        }

    def health(self) -> bool:
        return self.self_test()

    # ======================================================
    # Lifecycle
    # ======================================================

    def initialize(self) -> None:
        with self._lock:
            self._cache = OrderedDict()
            self._cache_size = max(0, self._cache_size)
            self.reset_metrics()

    def reset(self) -> None:
        self.reset_metrics()
        self.clear_cache()

    def shutdown(self) -> None:
        self.reset()

    def dispose(self) -> None:
        self.shutdown()

    def clone(self) -> CsvCodec:
        return CsvCodec(**self.configuration())

    # ======================================================
    # Runtime Export
    # ======================================================

    def export_runtime(self) -> dict[str, Any]:
        return {
            "runtime": self.runtime_information(),
            "statistics": self.statistics(),
            "performance": self.performance(),
            "diagnostics": self.diagnostics(),
        }

    def import_runtime(
        self,
        state: Mapping[str, Any],
    ) -> None:
        # Operational counters are intentionally not restored
        # from external runtime state.
        if not isinstance(state, Mapping):
            return

    # ======================================================
    # Format Information
    # ======================================================

    @staticmethod
    def file_extension() -> str:
        return ".csv"

    @staticmethod
    def supported_extensions() -> tuple[str, ...]:
        return (".csv", ".tsv")

    @staticmethod
    def detect_format(filename: str) -> str:
        return "csv"

    # ======================================================
    # Dialect Information
    # ======================================================

    def dialect(self) -> dict[str, Any]:
        return {
            "delimiter": self._delimiter,
            "quotechar": self._quotechar,
            "escapechar": self._escapechar,
            "lineterminator": self._lineterminator,
            "quoting": self._quoting,
            "skipinitialspace": self._skipinitialspace,
            "strict": self._strict,
            "doublequote": self._doublequote,
        }

    def csv_dialect(self) -> csv.Dialect:
        codec = self

        class AuraDialect(csv.Dialect):
            delimiter = codec._delimiter
            quotechar = codec._quotechar
            escapechar = codec._escapechar
            lineterminator = codec._lineterminator
            quoting = codec._quoting
            skipinitialspace = codec._skipinitialspace
            strict = codec._strict
            doublequote = codec._doublequote

        return AuraDialect

    # ======================================================
    # Alternate Constructors
    # ======================================================

    @classmethod
    def from_tsv(cls, **kwargs: Any) -> CsvCodec:
        kwargs["delimiter"] = "\t"
        return cls(**kwargs)

    @classmethod
    def from_semicolon(cls, **kwargs: Any) -> CsvCodec:
        kwargs["delimiter"] = ";"
        return cls(**kwargs)

    @classmethod
    def from_pipe(cls, **kwargs: Any) -> CsvCodec:
        kwargs["delimiter"] = "|"
        return cls(**kwargs)

    @classmethod
    def from_dialect(
        cls,
        dialect: str,
        **kwargs: Any,
    ) -> CsvCodec:
        loaded = csv.get_dialect(dialect)

        kwargs.setdefault("delimiter", loaded.delimiter)
        kwargs.setdefault("quotechar", loaded.quotechar)
        kwargs.setdefault("escapechar", loaded.escapechar)
        kwargs.setdefault("lineterminator", loaded.lineterminator)
        kwargs.setdefault("quoting", loaded.quoting)
        kwargs.setdefault("skipinitialspace", loaded.skipinitialspace)
        kwargs.setdefault("strict", loaded.strict)
        kwargs.setdefault("doublequote", loaded.doublequote)

        return cls(**kwargs)

    # ======================================================
    # Sampling / Sniffing
    # ======================================================

    def sniff(
        self,
        sample: str | bytes,
        *,
        delimiters: str | None = None,
    ) -> dict[str, Any]:
        if isinstance(sample, bytes):
            sample = sample.decode(self._encoding)

        try:
            dialect = csv.Sniffer().sniff(
                sample,
                delimiters=delimiters,
            )
            has_header = csv.Sniffer().has_header(sample)

            return {
                "delimiter": dialect.delimiter,
                "quotechar": dialect.quotechar,
                "escapechar": dialect.escapechar,
                "doublequote": dialect.doublequote,
                "skipinitialspace":
                    dialect.skipinitialspace,
                "quoting": dialect.quoting,
                "has_header": has_header,
            }
        except csv.Error as exc:
            raise DeserializationError(
                f"Unable to detect CSV dialect: {exc}"
            ) from exc

    # ======================================================
    # Sniffed Codec
    # ======================================================

    @classmethod
    def from_sample(
        cls,
        sample: str | bytes,
        *,
        delimiters: str | None = None,
        encoding: str = "utf-8",
    ) -> CsvCodec:
        probe = cls(encoding=encoding)
        detected = probe.sniff(
            sample,
            delimiters=delimiters,
        )
        return cls(
            encoding=encoding,
            delimiter=detected["delimiter"],
            quotechar=detected["quotechar"],
            escapechar=detected["escapechar"],
            lineterminator="\n",
            quoting=detected["quoting"],
            skipinitialspace=detected["skipinitialspace"],
            doublequote=detected["doublequote"],
        )

    # ======================================================
    # Iterative Reading
    # ======================================================

    def iter_rows(
        self,
        data: str | bytes,
        *,
        has_header: bool = True,
        fieldnames: Sequence[str] | None = None,
    ) -> Iterator[dict[str, Any]]:
        if isinstance(data, bytes):
            data = data.decode(self._encoding)

        stream = io.StringIO(data, newline="")

        if has_header:
            reader = csv.DictReader(
                stream,
                delimiter=self._delimiter,
                quotechar=self._quotechar,
                escapechar=self._escapechar,
                skipinitialspace=self._skipinitialspace,
                strict=self._strict,
                doublequote=self._doublequote,
            )
            for row in reader:
                yield dict(row)
            return

        if fieldnames is None:
            raise DeserializationError(
                "fieldnames are required for headerless CSV."
            )

        reader = csv.reader(
            stream,
            delimiter=self._delimiter,
            quotechar=self._quotechar,
            escapechar=self._escapechar,
            skipinitialspace=self._skipinitialspace,
            strict=self._strict,
            doublequote=self._doublequote,
        )

        for row in reader:
            yield dict(zip(fieldnames, row))

    # ======================================================
    # Chunked Reading
    # ======================================================

    def read_chunks(
        self,
        data: str | bytes,
        *,
        chunk_size: int = 1000,
        has_header: bool = True,
    ) -> Iterator[list[dict[str, Any]]]:
        if chunk_size <= 0:
            raise ValueError("chunk_size must be positive")

        chunk: list[dict[str, Any]] = []

        for row in self.iter_rows(
            data,
            has_header=has_header,
        ):
            chunk.append(row)

            if len(chunk) >= chunk_size:
                yield chunk
                chunk = []

        if chunk:
            yield chunk

    # ======================================================
    # Aggregation
    # ======================================================

    def group_rows(
        self,
        rows: Iterable[Mapping[str, Any]],
        key: str,
    ) -> dict[Any, list[dict[str, Any]]]:
        groups: dict[Any, list[dict[str, Any]]] = {}

        for row in rows:
            value = row.get(key)
            groups.setdefault(value, []).append(dict(row))

        return groups

    def unique_values(
        self,
        rows: Iterable[Mapping[str, Any]],
        key: str,
    ) -> list[Any]:
        result: list[Any] = []
        seen: set[str] = set()

        for row in rows:
            value = row.get(key)
            marker = repr(value)

            if marker not in seen:
                seen.add(marker)
                result.append(value)

        return result

    # ======================================================
    # Row Conversion
    # ======================================================

    def rows_to_tuples(
        self,
        rows: Iterable[Mapping[str, Any]],
        columns: Sequence[str],
    ) -> list[tuple[Any, ...]]:
        names = [str(column) for column in columns]
        return [
            tuple(row.get(name) for name in names)
            for row in rows
        ]

    def tuples_to_rows(
        self,
        rows: Iterable[Sequence[Any]],
        columns: Sequence[str],
    ) -> list[dict[str, Any]]:
        names = [str(column) for column in columns]
        return [
            dict(zip(names, row))
            for row in rows
        ]

    # ======================================================
    # CSVL Helpers
    # ======================================================

    def serialize_lines(
        self,
        rows: Iterable[Mapping[str, Any]],
    ) -> str:
        """
        Serialize records as independent CSV records.

        This helper intentionally omits a header.
        """

        return self.serialize(
            list(rows),
            include_header=False,
        )

    def deserialize_lines(
        self,
        data: str | bytes,
        fieldnames: Sequence[str],
    ) -> list[dict[str, Any]]:
        return self.deserialize(
            data,
            fieldnames=fieldnames,
            has_header=False,
        )

    # ======================================================
    # Formula / Spreadsheet Safety
    # ======================================================

    @staticmethod
    def sanitize_formula_cell(
        value: Any,
        *,
        prefix: str = "'",
    ) -> Any:
        """
        Protect spreadsheet consumers from formula-like cells.

        This does not alter ordinary values.
        """

        if not isinstance(value, str):
            return value

        stripped = value.lstrip()

        if stripped.startswith((
            "=",
            "+",
            "-",
            "@",
        )):
            return prefix + value

        return value

    def sanitize_rows(
        self,
        rows: Iterable[Mapping[str, Any]],
    ) -> list[dict[str, Any]]:
        return [
            {
                str(key): self.sanitize_formula_cell(value)
                for key, value in row.items()
            }
            for row in rows
        ]

    # ======================================================
    # JSON-Friendly Conversion
    # ======================================================

    def to_json_compatible(
        self,
        rows: Iterable[Mapping[str, Any]],
    ) -> list[dict[str, Any]]:
        return json.loads(
            json.dumps(
                [dict(row) for row in rows],
                default=str,
                ensure_ascii=False,
            )
        )

    # ======================================================
    # Size Helpers
    # ======================================================

    def serialized_size(
        self,
        value: Any,
        *,
        fieldnames: Sequence[str] | None = None,
    ) -> int:
        return len(
            self.serialize(
                value,
                fieldnames=fieldnames,
            ).encode(self._encoding)
        )

    def compressed_size(
        self,
        value: Any,
        *,
        fieldnames: Sequence[str] | None = None,
    ) -> int:
        return len(
            self.serialize_compressed(
                value,
                fieldnames=fieldnames,
            )
        )

    # ======================================================
    # Compression Ratio
    # ======================================================

    def compression_ratio(
        self,
        value: Any,
        *,
        fieldnames: Sequence[str] | None = None,
    ) -> float:
        raw = self.serialized_size(
            value,
            fieldnames=fieldnames,
        )

        compressed = self.compressed_size(
            value,
            fieldnames=fieldnames,
        )

        if raw == 0:
            return 1.0

        return compressed / raw

    # ======================================================
    # Schema Summary
    # ======================================================

    def schema_summary(
        self,
        rows: Sequence[Mapping[str, Any]],
    ) -> dict[str, Any]:
        fields = self.infer_fieldnames(rows)

        types: dict[str, set[str]] = {
            field: set()
            for field in fields
        }

        nullable: dict[str, bool] = {
            field: False
            for field in fields
        }

        for row in rows:
            for field in fields:
                value = row.get(field)

                if value is None or value == "":
                    nullable[field] = True
                else:
                    types[field].add(
                        type(value).__name__
                    )

        return {
            "fields": fields,
            "field_count": len(fields),
            "row_count": len(rows),
            "types": {
                field: sorted(values)
                for field, values in types.items()
            },
            "nullable": nullable,
        }

    # ======================================================
    # Required / Optional Fields
    # ======================================================

    def required_fields(
        self,
        rows: Sequence[Mapping[str, Any]],
    ) -> list[str]:
        if not rows:
            return []

        fields = self.infer_fieldnames(rows)

        return [
            field
            for field in fields
            if all(
                row.get(field) not in (None, "")
                for row in rows
            )
        ]

    def optional_fields(
        self,
        rows: Sequence[Mapping[str, Any]],
    ) -> list[str]:
        fields = self.infer_fieldnames(rows)
        required = set(self.required_fields(rows))

        return [
            field
            for field in fields
            if field not in required
        ]

    # ======================================================
    # Data Quality
    # ======================================================

    def data_quality_report(
        self,
        rows: Sequence[Mapping[str, Any]],
    ) -> dict[str, Any]:
        fields = self.infer_fieldnames(rows)
        missing: dict[str, int] = {
            field: 0
            for field in fields
        }

        empty: dict[str, int] = {
            field: 0
            for field in fields
        }

        for row in rows:
            for field in fields:
                if field not in row:
                    missing[field] += 1
                elif row[field] is None:
                    empty[field] += 1
                elif isinstance(row[field], str) and not row[field].strip():
                    empty[field] += 1

        return {
            "rows": len(rows),
            "fields": len(fields),
            "missing": missing,
            "empty": empty,
            "required_fields": self.required_fields(rows),
            "optional_fields": self.optional_fields(rows),
        }

    # ======================================================
    # Lifecycle Self-Test
    # ======================================================

    def self_test(self) -> bool:
        sample = [
            {
                "framework": "AURA",
                "version": "1",
                "enabled": "true",
            },
            {
                "framework": "AURA",
                "version": "2",
                "enabled": "false",
            },
        ]

        try:
            encoded = self.serialize(sample)
            decoded = self.deserialize(encoded)

            if decoded != sample:
                return False

            compressed = self.serialize_compressed(sample)
            restored = self.deserialize_compressed(compressed)

            if restored != sample:
                return False

            return self.validate_headers(
                encoded,
                ["framework", "version", "enabled"],
            )

        except Exception:
            return False

    # ======================================================
    # Representation
    # ======================================================

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"format='{self.format}', "
            f"delimiter={self._delimiter!r}, "
            f"encoding='{self._encoding}')"
        )

    def __str__(self) -> str:
        return self.__repr__()

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, CsvCodec):
            return False

        return (
            self.format == other.format
            and self.configuration()
            == other.configuration()
        )

    def __hash__(self) -> int:
        return hash(
            (
                self.format,
                self._delimiter,
                self._quotechar,
                self._encoding,
            )
        )


# ==========================================================
# Default Codec
# ==========================================================

csv_codec = CsvCodec()


# ==========================================================
# Public API
# ==========================================================

__all__ = [
    "CsvCodec",
    "csv_codec",
]
