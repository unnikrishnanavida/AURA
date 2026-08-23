"""Storage adapters for aura-memory."""

from __future__ import annotations

import json
import os
import sqlite3
import time
from typing import Any, Optional, Protocol


class StorageAdapter(Protocol):
    def get(self, key: str) -> Optional[Any]:
        ...

    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        ...

    def delete(self, key: str) -> None:
        ...


class SQLiteAdapter:
    def __init__(self, db_path: str, table: str = "kv_store") -> None:
        self._db_path = os.path.abspath(db_path)
        self._table = table
        self._conn = sqlite3.connect(self._db_path, check_same_thread=False)
        self._conn.execute(
            f"CREATE TABLE IF NOT EXISTS {self._table} (key TEXT PRIMARY KEY, value TEXT, expire_at REAL)"
        )
        self._conn.commit()

    def _now(self) -> float:
        return time.time()

    def get(self, key: str) -> Optional[Any]:
        cursor = self._conn.execute(
            f"SELECT value, expire_at FROM {self._table} WHERE key = ?", (key,)
        )
        row = cursor.fetchone()
        if row is None:
            return None
        value, expire_at = row
        if expire_at is not None and expire_at <= self._now():
            self.delete(key)
            return None
        try:
            return json.loads(value)
        except Exception:
            return json.loads(value or "null")

    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        expire_at = None if ttl is None else self._now() + float(ttl)
        payload = json.dumps(value, default=str)
        self._conn.execute(
            f"INSERT OR REPLACE INTO {self._table} (key, value, expire_at) VALUES (?, ?, ?)",
            (key, payload, expire_at),
        )
        self._conn.commit()

    def delete(self, key: str) -> None:
        self._conn.execute(f"DELETE FROM {self._table} WHERE key = ?", (key,))
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()


class RedisAdapter:
    def __init__(self, url: str):
        try:
            import redis  # type: ignore[import]
        except ImportError as exc:
            raise RuntimeError("Redis adapter requires the 'redis' package") from exc
        self._client = redis.from_url(url)

    def get(self, key: str) -> Optional[Any]:
        raw = self._client.get(key)
        if raw is None:
            return None
        try:
            return json.loads(raw)
        except Exception:
            return raw.decode("utf-8")

    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        payload = json.dumps(value, default=str)
        if ttl is None:
            self._client.set(key, payload)
        else:
            self._client.setex(key, int(ttl), payload)

    def delete(self, key: str) -> None:
        self._client.delete(key)


__all__ = ["StorageAdapter", "SQLiteAdapter", "RedisAdapter"]
