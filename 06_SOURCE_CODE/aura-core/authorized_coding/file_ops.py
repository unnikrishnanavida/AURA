"""Boundary-checked file operations for authorized coding.

Every operation re-validates the workspace boundary before touching the
filesystem. These helpers are consumed by :mod:`authorized_coding.engine`.
"""

from __future__ import annotations

import os

from .models import ResultStatus, ActionResult
from .workspace import PathViolation, WorkspaceRoot

__all__ = [
    "PatchError",
    "apply_patch",
    "delete_file",
    "list_files",
    "read_file",
    "write_text",
    "patch_file",
    "create_directory",
    "count_hunks",
]


class PatchError(ValueError):
    """A unified diff could not be applied cleanly."""


def apply_patch(old_text: str, diff: str, *, expect_new: str | None = None) -> str:
    """Apply a unified diff to *old_text* and return the new text.

    The diff must cover the whole file (every old line is consumed); an
    optional *expect_new* verifies the result. Raises :class:`PatchError` on
    any mismatch.
    """
    old_lines = old_text.splitlines()
    new_lines: list[str] = []
    cursor = 0
    lines = diff.splitlines()
    i, n = 0, len(lines)

    while i < n:
        line = lines[i]
        if not line.startswith("@@"):
            i += 1
            continue
        match = _PATTERN_HUNK_HEADER.match(line[2:].strip())
        if not match:
            raise PatchError(f"bad hunk header: {line!r}")
        old_start = int(match.group(1)) - 1  # 1-based -> 0-based
        old_count = int(match.group(2)) if match.group(2) else None
        i += 1
        hunk_lines: list[str] = []
        while i < n and not lines[i].startswith("@@"):
            hunk_lines.append(lines[i])
            i += 1
        if cursor != old_start:
            raise PatchError(
                f"hunk starts at line {old_start + 1} but file cursor is {cursor + 1}"
            )
        old_consumed = 0
        for hunk_line in hunk_lines:
            if hunk_line.startswith(" "):
                expected = hunk_line[1:]
                if cursor >= len(old_lines) or old_lines[cursor] != expected:
                    raise PatchError(
                        f"context mismatch at line {cursor + 1}: expected {expected!r}, "
                        f"file has {old_lines[cursor]!r}"
                    )
                new_lines.append(expected)
                cursor += 1
                old_consumed += 1
            elif hunk_line.startswith("-") and len(hunk_line) > 1:
                limit = old_count if old_count is not None else 10_000_000
                if old_consumed >= limit:
                    raise PatchError("hunk exceeds its declared old-line count")
                if cursor >= len(old_lines):
                    raise PatchError(f"delete beyond end of file at line {cursor + 1}")
                cursor += 1
                old_consumed += 1
            elif hunk_line.startswith("+") and len(hunk_line) > 1:
                new_lines.append(hunk_line[1:])
            else:
                raise PatchError(f"unknown hunk line: {hunk_line!r}")
    if cursor != len(old_lines):
        raise PatchError(
            f"patch does not cover the whole file: {len(old_lines) - cursor} old line(s) left over"
        )
    result = "".join(new_lines)
    if expect_new is not None and result != expect_new:
        raise PatchError("patch does not reproduce the expected content")
    return result


