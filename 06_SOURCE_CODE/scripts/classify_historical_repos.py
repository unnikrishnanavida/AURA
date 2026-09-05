"""Classify the historical AURA repositories.

Counts files and checks Python syntax so the recovery analysis is grounded in
measurement rather than impressions. The output feeds the business-wide
RECOVERY analysis documented alongside the canonical runtime.
"""

from __future__ import annotations

import ast
import pathlib
import sys

REPOS = ("aura-memory", "aura-learning", "aura_reasoning", "aura-reasoning(2)")

BASE = pathlib.Path(__file__).resolve().parents[1]


def analyze(repo: str) -> dict[str, object]:
    root = BASE / repo
    py_files = [
        f for f in root.rglob("*.py") if "__pycache__" not in str(f)
    ]
    parse_ok = 0
    parse_fail = 0
    empty_files = 0
    dead_branches = 0
    imports_referencing_runtime = 0
    for f in py_files:
        try:
            text = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            parse_fail += 1
            continue
        if not text.strip():
            empty_files += 1
            continue
        dead_branches += text.count('if "') + text.count("if '")
        imports_referencing_runtime += text.count("aura_learning.runtime")
        try:
            ast.parse(text)
            parse_ok += 1
        except SyntaxError:
            parse_fail += 1
    return {
        "repo": repo,
        "python_files": len(py_files),
        "parse_ok": parse_ok,
        "parse_fail": parse_fail,
        "empty_files": empty_files,
        "approx_dead_branches": dead_branches,
        "aura_learning_runtime_refs": imports_referencing_runtime,
    }


def main() -> int:
    for repo in REPOS:
        result = analyze(repo)
        print(
            f"{result['repo']}: files={result['python_files']} "
            f"parse_ok={result['parse_ok']} parse_fail={result['parse_fail']} "
            f"empty={result['empty_files']} dead_branch_lines={result['approx_dead_branches']} "
            f"runtime_refs={result['aura_learning_runtime_refs']}"
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())