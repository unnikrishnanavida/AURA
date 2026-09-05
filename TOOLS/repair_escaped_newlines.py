"""Repair generated files that contain literal backslash-n instead of real newlines.

Handles .py (compile-verified) and other text files (.toml/.md/.json/.yaml/.txt).
A file is a repair candidate when it consists of effectively one physical line
(no real newline byte) yet contains literal backslash-n sequences.

Usage: python repair_escaped_newlines.py <target-root>   (skip list built-in)
"""

from __future__ import annotations

import pathlib
import py_compile
import sys

_SKIP_DIRS = {"__pycache__", "node_modules", ".venv"}
_SKIP_ROOTS = {"aura-memory", "aura-learning", "aura-brain"}
_TEXT_SUFFIXES = {".py", ".toml", ".md", ".json", ".yaml", ".yml", ".txt", ".cfg", ".ini", ".sh"}


def _compile_ok(path: pathlib.Path) -> bool:
    try:
        py_compile.compile(str(path), doraise=True, cfile=str(path) + "c")
        return True
    except Exception:
        return False


def repair(root: pathlib.Path) -> None:
    fixed: list[str] = []
    scanned = 0
    for path in root.rglob("*"):
        if not path.is_file() or path.suffix not in _TEXT_SUFFIXES:
            continue
        rel = path.relative_to(root)
        if any(part in _SKIP_DIRS for part in path.parts):
            continue
        if any(part in _SKIP_ROOTS for part in path.parts):
            continue
        scanned += 1
        data = path.read_bytes()
        text = data.decode("utf-8", errors="replace")

        needs_repair = "\n" not in text
        if path.suffix == ".py":
            if _compile_ok(path) or "\\n" not in text:
                continue
        elif not needs_repair or "\\n" not in text:
            continue

        repaired = text.replace("\\n", "\n").replace('\\"', '"')
        candidate = pathlib.Path(str(path) + ".repair")
        candidate.write_text(repaired, encoding="utf-8")
        ok = True
        if path.suffix == ".py" and not _compile_ok(candidate):
            ok = False
        if ok:
            path.write_text(repaired, encoding="utf-8")
            fixed.append(str(path.relative_to(root)))
        candidate.unlink(missing_ok=True)

    print(f"scanned={scanned} fixed={len(fixed)}")
    for item in fixed:
        print("  fixed:", item)


if __name__ == "__main__":
    repair(pathlib.Path(sys.argv[1]).resolve())