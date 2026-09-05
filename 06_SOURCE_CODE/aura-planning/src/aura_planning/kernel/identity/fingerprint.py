from __future__ import annotations
import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import asdict, is_dataclass
from typing import Any

def _canonical(value: Any) -> Any:
    if is_dataclass(value):
        return _canonical(asdict(value))
    if isinstance(value, Mapping):
        return {str(k): _canonical(value[k]) for k in sorted(value, key=str)}
    if isinstance(value, (set, frozenset)):
        return sorted((_canonical(v) for v in value), key=repr)
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return [_canonical(v) for v in value]
    if isinstance(value, bytes):
        return value.hex()
    if isinstance(value, float) and value != value:
        return "NaN"
    return value

def canonical_json(value: Any) -> str:
    return json.dumps(_canonical(value), sort_keys=True, separators=(",", ":"), default=str)

def fingerprint(value: Any, algorithm: str = "sha256") -> str:
    try:
        digest = hashlib.new(algorithm)
    except ValueError as exc:
        raise ValueError(f"unsupported hash algorithm: {algorithm}") from exc
    digest.update(canonical_json(value).encode())
    return digest.hexdigest()
