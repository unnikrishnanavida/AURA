"""Deterministic random sources.

Reasoning, planning, and memory engines must be reproducible when configured
with a seed. `SeededRandom` wraps Python's random.Random in the AURA
:class:`RandomSource` protocol; `SecureRandom` delegates to the system CSPRNG.
"""

from __future__ import annotations

import random
import secrets
from collections.abc import Sequence
from typing import Any, Protocol, runtime_checkable


@runtime_checkable
class RandomSource(Protocol):
    def random(self) -> float: ...

    def randint(self, low: int, high: int) -> int: ...

    def choice(self, seq: Sequence[Any]) -> Any: ...

    def shuffle(self, seq: list[Any]) -> None: ...


class SeededRandom:
    """Deterministic pseudo-random source seeded for reproducibility."""

    def __init__(self, seed: int) -> None:
        self._rng = random.Random(seed)  # noqa: S311 - deterministic, intentionally non-cryptographic

    def random(self) -> float:
        return self._rng.random()

    def randint(self, low: int, high: int) -> int:
        return self._rng.randint(low, high)

    def choice(self, seq: Sequence[Any]) -> Any:
        return self._rng.choice(seq)

    def shuffle(self, seq: list[Any]) -> None:
        self._rng.shuffle(seq)


class SecureRandom:
    """Cryptographically secure random source (not reproducible)."""

    def random(self) -> float:
        return secrets.randbelow(1 << 53) / (1 << 53)

    def randint(self, low: int, high: int) -> int:
        return secrets.randbelow(high - low + 1) + low

    def choice(self, seq: Sequence[Any]) -> Any:
        return seq[secrets.randbelow(len(seq))]

    def shuffle(self, seq: list[Any]) -> None:
        for i in range(len(seq) - 1, 0, -1):
            j = secrets.randbelow(i + 1)
            seq[i], seq[j] = seq[j], seq[i]


__all__ = ["RandomSource", "SecureRandom", "SeededRandom"]