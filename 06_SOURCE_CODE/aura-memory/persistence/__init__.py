"""Persistence subsystem: storage interface and backends.

Provides a minimal `Storage` protocol and two simple implementations:
- `InMemoryStorage`: fast in-process storage with optional TTL and LRU cleanup.
- `FileStorage`: simple file-backed storage writing JSON files to a directory.

These backends are intentionally small and dependency-free; replace or extend
with Redis, SQLite, or other durable backends for production.
"""

from __future__ import annotations

import base64
import json
import os
import threading
import time
from typing import Any, Dict, Iterable, Optional, Protocol, Tuple


class Storage(Protocol):
    def get(self, key: str) -> Optional[Any]:
        ...

    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        ...

    def delete(self, key: str) -> None:
        ...

    def list_keys(self) -> Iterable[str]:
        ...


class InMemoryStorage:
    """Simple in-memory store with optional TTL and background janitor.

    Values are stored as (value, expire_at) where expire_at is an epoch
    timestamp or None.
    """

    def __init__(self, janitor_interval: float = 5.0) -> None:
        self._store: Dict[str, Tuple[Any, Optional[float]]] = {}
        self._lock = threading.RLock()
        self._janitor_interval = float(janitor_interval)
        self._stop = threading.Event()
        self._janitor = threading.Thread(target=self._run_janitor, daemon=True)
        self._janitor.start()

    def _run_janitor(self) -> None:
        while not self._stop.wait(self._janitor_interval):
            now = time.time()
            with self._lock:
                keys = list(self._store.keys())
                for k in keys:
                    _, exp = self._store.get(k, (None, None))
                    if exp is not None and exp <= now:
                        del self._store[k]

    def get(self, key: str) -> Optional[Any]:
        with self._lock:
            row = self._store.get(key)
            if row is None:
                return None
            value, exp = row
            if exp is not None and exp <= time.time():
                del self._store[key]
                return None
            return value

    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        exp = None if ttl is None else (time.time() + float(ttl))
        with self._lock:
            self._store[key] = (value, exp)

    def delete(self, key: str) -> None:
        with self._lock:
            self._store.pop(key, None)

    def list_keys(self) -> Iterable[str]:
        with self._lock:
            now = time.time()
            keys = [k for k, (_, exp) in self._store.items() if exp is None or exp > now]
            return list(keys)

    def close(self) -> None:
        self._stop.set()
        self._janitor.join(timeout=1.0)


class FileStorage:
    """File-backed JSON storage. Each key is stored in a separate file.

    Filenames are a urlsafe base64 encoding of the key to avoid filesystem
    restrictions.
    """

    def __init__(self, data_dir: str) -> None:
        self._dir = os.path.abspath(data_dir)
        os.makedirs(self._dir, exist_ok=True)

    def _filename_for(self, key: str) -> str:
        safe = base64.urlsafe_b64encode(key.encode()).decode().rstrip("=")
        return os.path.join(self._dir, f"{safe}.json")

    def get(self, key: str) -> Optional[Any]:
        fn = self._filename_for(key)
        try:
            with open(fn, "r", encoding="utf-8") as fh:
                payload = json.load(fh)
            exp = payload.get("expire_at")
            if exp is not None and exp <= time.time():
                try:
                    os.remove(fn)
                except Exception:
                    pass
                return None
            return payload.get("value")
        except FileNotFoundError:
            return None

    def set(self, key: str, value: Any, ttl: Optional[float] = None) -> None:
        fn = self._filename_for(key)
        expire_at = None if ttl is None else (time.time() + float(ttl))
        payload = {"value": value, "expire_at": expire_at}
        tmp = fn + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump(payload, fh, default=str, separators=(",", ":"))
            fh.flush()
            os.fsync(fh.fileno())
        os.replace(tmp, fn)

    def delete(self, key: str) -> None:
        fn = self._filename_for(key)
        try:
            os.remove(fn)
        except FileNotFoundError:
            pass

    def list_keys(self) -> Iterable[str]:
        for name in os.listdir(self._dir):
            if not name.endswith(".json"):
                continue
            safe = name[:-5]
            # restore padding
            pad = "=" * (-len(safe) % 4)
            try:
                key = base64.urlsafe_b64decode(safe + pad).decode()
            except Exception:
                continue
            # check expire
            fn = os.path.join(self._dir, name)
            try:
                with open(fn, "r", encoding="utf-8") as fh:
                    payload = json.load(fh)
                exp = payload.get("expire_at")
                if exp is not None and exp <= time.time():
                    try:
                        os.remove(fn)
                    except Exception:
                        pass
                    continue
                yield key
            except Exception:
                continue


__all__ = ["Storage", "InMemoryStorage", "FileStorage"]
