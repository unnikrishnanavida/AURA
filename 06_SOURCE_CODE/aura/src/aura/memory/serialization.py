"""Memory persistence serialization.

Maps :class:`MemoryEntry` to a stable, JSON-compatible row format that every
persistent backend shares. A backend only needs to store these values and
round-trip them through :func:`row_to_entry`; this module is therefore the
PostgreSQL-ready interface as well as the SQLite row definition.

The row format is versioned via ``MEMORY_SCHEMA_VERSION``. Changing the format
requires a coordinated migration so old rows remain readable.
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from datetime import UTC, datetime
from typing import Any

from aura.foundation.ids import ExecutionId, MemoryId
from aura.memory.models import (
    LinkKind,
    MemoryConfidence,
    MemoryEntry,
    MemoryStatus,
    MemoryType,
    Provenance,
    RetentionPolicy,
    Sensitivity,
)

MEMORY_SCHEMA_VERSION = 1


def _dt(value: datetime | None) -> str | None:
    return value.astimezone(UTC).isoformat() if value is not None else None


def _dt_parse(value: str | None, *, field: str) -> datetime | None:
    if value is None or value == "":
        return None
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"corrupted timestamp for {field}: {value!r}") from exc
    return parsed if parsed.tzinfo is not None else parsed.replace(tzinfo=UTC)
def entry_to_row(entry: MemoryEntry) -> dict[str, Any]:
    """Serialize one entry into the stable row dictionary."""
    return {
        "id": str(entry.id),
        "key": entry.key,
        "kind": entry.kind.value,
        "content": json.dumps(entry.content, sort_keys=True),
        "importance": entry.importance,
        "confidence_fact": entry.confidence.fact,
        "confidence_source": entry.confidence.source,
        "confidence_freshness": entry.confidence.freshness,
        "confidence_relevance": entry.confidence.relevance,
        "provenance_source": entry.provenance.source,
        "provenance_execution_id": (
            str(entry.provenance.execution_id) if entry.provenance.execution_id is not None else None
        ),
        "provenance_creator": entry.provenance.creator,
        "provenance_details": json.dumps(entry.provenance.details, sort_keys=True),
        "created_at": _dt(entry.created_at),
        "last_access": _dt(entry.last_access),
        "access_count": entry.access_count,
        "tags": json.dumps(list(entry.tags)),
        "expires_at": _dt(entry.expires_at),
        "links": json.dumps({str(k): v.value for k, v in entry.links.items()}, sort_keys=True),
        "sensitivity": entry.sensitivity.value,
        "status": entry.status.value,
        "version": entry.version,
        "supersedes": str(entry.supersedes) if entry.supersedes is not None else None,
        "observed_at": _dt(entry.observed_at),
        "retention_ttl_seconds": entry.retention.ttl_seconds if entry.retention is not None else None,
        "retention_max_versions": entry.retention.max_versions if entry.retention is not None else None,
        "schema_version": MEMORY_SCHEMA_VERSION,
    }


def row_to_entry(row: Mapping[str, Any]) -> MemoryEntry:
    """Reconstruct one entry from a row dictionary.

    Raises ``ValueError`` with a descriptive message when the row is corrupted
    (unparseable JSON, invalid timestamp, out-of-range value) so corrupt state
    never silently propagates.
    """
    created = _required_dt(row.get("created_at"), "created_at")
    last_access = _required_dt(row.get("last_access"), "last_access")

    try:
        content = json.loads(row.get("content") or "{}")
    except json.JSONDecodeError as exc:
        raise ValueError(f"corrupted content JSON for {row.get('id')}: {exc}") from exc

    try:
        tags = tuple(json.loads(row.get("tags") or "[]"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"corrupted tags JSON for {row.get('id')}: {exc}") from exc

    try:
        links = {str(k): LinkKind(v) for k, v in json.loads(row.get("links") or "{}").items()}
    except (json.JSONDecodeError, ValueError) as exc:
        raise ValueError(f"corrupted links JSON for {row.get('id')}: {exc}") from exc

    try:
        details = json.loads(row.get("provenance_details") or "{}")
    except json.JSONDecodeError as exc:
        raise ValueError(f"corrupted provenance details JSON for {row.get('id')}: {exc}") from exc

    retention = None
    ttl = row.get("retention_ttl_seconds")
    max_versions = row.get("retention_max_versions")
    if ttl is not None or max_versions is not None:
        retention = RetentionPolicy(
            ttl_seconds=float(ttl) if ttl is not None else None,
            max_versions=int(max_versions or 1),
        )

    return MemoryEntry(
        id=MemoryId.from_str(str(row["id"])),
        key=str(row["key"]),
        kind=MemoryType(str(row["kind"])),
        content=dict(content) if isinstance(content, dict) else {"value": content},
        importance=float(row["importance"]),
        confidence=MemoryConfidence(
            fact=float(row["confidence_fact"]),
            source=float(row["confidence_source"]),
            freshness=float(row["confidence_freshness"]),
            relevance=float(row["confidence_relevance"]),
        ),
        provenance=Provenance(
            source=str(row["provenance_source"]),
            execution_id=(
                ExecutionId.from_str(str(row["provenance_execution_id"]))
                if row.get("provenance_execution_id")
                else None
            ),
            creator=str(row["provenance_creator"]),
            details=details if isinstance(details, dict) else {},
        ),
        created_at=created,
        last_access=last_access,
        access_count=int(row.get("access_count") or 0),
        tags=tags,
        expires_at=_dt_parse(row.get("expires_at"), field="expires_at"),
        links=links,
        sensitivity=Sensitivity(str(row["sensitivity"])),
        status=MemoryStatus(str(row["status"])),
        version=int(row.get("version") or 1),
        supersedes=MemoryId.from_str(str(row["supersedes"])) if row.get("supersedes") else None,
        observed_at=_dt_parse(row.get("observed_at"), field="observed_at"),
        retention=retention,
    )


def _required_dt(value: str | None, field: str) -> datetime:
    parsed = _dt_parse(value, field=field)
    if parsed is None:
        raise ValueError(f"corrupted row: required timestamp {field} is missing")
    return parsed


__all__ = ["MEMORY_SCHEMA_VERSION", "entry_to_row", "row_to_entry"]