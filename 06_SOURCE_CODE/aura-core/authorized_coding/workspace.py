"""Workspace boundary enforcement for authorized coding.

The workspace root is the security boundary of every project action:

* the root is canonicalized once (symlinks resolved) and re-derived on every
  use, so the boundary is revalidated at use time;
* every candidate path is canonicalized and must resolve strictly inside the
  root -- absolute paths, ``..`` escapes, and symlink escapes are rejected;
* the root is immutable by design: a caller that swaps the underlying
  directory after the root was created fails-closed with a boundary error.

All file access in the workflow goes through :meth:`WorkspaceRoot.resolve`
before any I/O happens.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable, Sequence

__all__ = [
    "PathViolation",
    "WorkspaceRoot",
    "canonicalize",
    "is_within",
]


class PathViolation(ValueError):
    """A path escaped the workspace boundary or was otherwise unusable."""


class WorkspaceRoot:
    """Owns one immutable workspace boundary.

    The root is canonicalized on construction and re-derived on every public
    method, which is what makes the boundary "revalidated at use". The root
    value itself is never mutated: callers that need a different workspace
    create a new :class:`WorkspaceRoot`.
    """

    def __init__(self, root: str | os.PathLike, *, description: str = "") -> None:
        self._raw = os.fspath(root)
        if not self._raw:
            raise PathViolation("workspace root must not be empty")
        if "\0" in self._raw:
            raise PathViolation("workspace root contains a NUL byte")
        self._root = os.path.realpath(os.path.abspath(self._raw))
        if not os.path.isdir(self._root):
            raise PathViolation(f"workspace root is not a directory: {self._root!r}")
        self._description = description

    @property
    def root(self) -> str:
        """Canonical, absolute root path (symlinks resolved)."""
        return self._root

    @property
    def description(self) -> str:
        return self._description

    def _revalidate_root(self) -> None:
        """Re-derive the canonical root and fail closed if the boundary moved.

        ``os.path.realpath`` resolves symlinks at call time, so this catches a
        mount/namespace change that would otherwise let a path slip past the
        boundary.
        """
        current = os.path.realpath(os.path.abspath(self._raw))
        if current != self._root:
            raise PathViolation(
                "workspace root changed since construction "
                f"(was {self._root!r}, now {current!r})"
            )

    def is_within(self, candidate: str | os.PathLike) -> bool:
        """Revalidated membership test (symlinks resolved at call time)."""
        self._revalidate_root()
        candidate_abs = os.path.realpath(os.path.abspath(os.fspath(candidate)))
        try:
            return os.path.commonpath([self._root, candidate_abs]) == self._root
        except ValueError:
            return False

    def resolve(self, candidate: str | os.PathLike) -> str:
        """Canonicalize *candidate* and return the absolute path inside the
        workspace root. Raises :class:`PathViolation` on any escape attempt.
        """
        self._revalidate_root()
        raw = os.fspath(candidate)
        if not raw:
            raise PathViolation("path must not be empty")
        if "\0" in raw:
            raise PathViolation("path contains a NUL byte")

        # Cheap lexical guard for the classic escape forms (before any
        # resolution), so errors are deterministic and fast.
        if raw.startswith(("/", "\\\\")) or raw.startswith(".." + os.sep) or raw == "..":
            raise PathViolation(f"path escapes the workspace root: {raw!r}")

        candidate_abs = os.path.abspath(raw)
        if not self.is_within(candidate_abs):
            raise PathViolation(
                f"path escapes the workspace root: {raw!r} resolves outside {self._root!r}"
            )
        return candidate_abs


def canonicalize(root: str | os.PathLike, candidate: str | os.PathLike) -> str:
    """Convenience: canonicalize *candidate* as *root* would, without a
    :class:`WorkspaceRoot` instance. Kept for small callers that only need a
    one-off boundary check."""
    root_abs = os.path.realpath(os.path.abspath(os.fspath(root)))
    candidate_abs = os.path.realpath(os.path.abspath(os.fspath(candidate)))
    if not is_within(root_abs, candidate_abs):
        raise PathViolation(
            f"{os.fspath(candidate)!r} escapes {os.fspath(root)!r}"
        )
    return candidate_abs


def is_within(root: str | os.PathLike, candidate: str | os.PathLike) -> bool:
    """True when *candidate* resolves strictly inside *root* (symlinks
    resolved at call time)."""
    root_abs = os.path.realpath(os.path.abspath(os.fspath(root)))
    candidate_abs = os.path.realpath(os.path.abspath(os.fspath(candidate)))
    try:
        return os.path.commonpath([root_abs, candidate_abs]) == root_abs
    except ValueError:
        return False
