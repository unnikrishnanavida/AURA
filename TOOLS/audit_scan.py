"""AURA read-only audit scanner: classify every tracked .py in 06_SOURCE_CODE.

Categories: EMPTY | MODULE_SHELL | PLACEHOLDER | SPARSE | REAL | BROKEN_SYNTAX
"""
from __future__ import annotations

import ast
import pathlib
import subprocess
from collections import Counter, defaultdict

ROOT = pathlib.Path(r"E:\AURA")
TRIVIAL_RETURNS = {"True", "False", "None", "0", "1", "-1", "{}", "[]", '""', "''"}


def tracked_files() -> list[str]:
    out = subprocess.run(
        ["git", "-C", str(ROOT), "ls-files", "06_SOURCE_CODE"],
        capture_output=True, text=True, check=True,
    ).stdout.splitlines()
    return [p for p in out if p.endswith(".py") and "node_modules" not in p and "__pycache__" not in p]


def _body_trivial(body: list[ast.stmt]) -> bool:
    if not body:
        return True
    if len(body) == 1:
        n = body[0]
        if isinstance(n, ast.Expr) and isinstance(n.value, ast.Constant) and isinstance(n.value.value, str):
            return True  # docstring only
        if isinstance(n, ast.Pass):
            return True
        if isinstance(n, ast.Return):
            v = n.value
            if v is None:
                return True
            if isinstance(v, ast.Constant) and str(v.value) in TRIVIAL_RETURNS:
                return True
            if isinstance(v, ast.Name) and v.id in {"True", "False", "None"}:
                return True
            if isinstance(v, (ast.Dict, ast.List, ast.Tuple)) and not list(ast.walk(v))[1:]:
                return True
    return False


def _has_logic(fn: ast.FunctionDef | ast.AsyncFunctionDef) -> bool:
    for node in ast.walk(fn):
        if isinstance(node, (ast.While, ast.For, ast.If, ast.Raise)):
            return True
        if isinstance(node, ast.Call):
            return True
        if isinstance(node, ast.BinOp) or isinstance(node, (ast.Add, ast.Sub, ast.Mult)):
            return True
        if isinstance(node, (ast.Assign, ast.AnnAssign)):
            return True
        if isinstance(node, ast.Return):
            v = node.value
            if v is None:
                continue
            if isinstance(v, ast.Constant) and str(v.value) in TRIVIAL_RETURNS:
                continue
            if isinstance(v, ast.Name) and v.id in {"True", "False", "None"}:
                continue
            if isinstance(v, (ast.Dict, ast.List, ast.Tuple)) and not list(ast.walk(v))[1:]:
                continue
            return True
    return False


def classify(path: pathlib.Path) -> str:
    try:
        raw = path.read_bytes()
    except OSError:
        return "EMPTY"
    if not raw.strip():
        return "EMPTY"
    try:
        tree = ast.parse(raw.decode("utf-8", errors="replace"))
    except SyntaxError:
        return "BROKEN_SYNTAX"

    total = trivial = 0
    has_logic = False
    has_placeholder = False
    mod_logic = False
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            total += 1
            body = node.body[1:] if (node.body and isinstance(node.body[0], ast.Expr)
                                     and isinstance(node.body[0].value, ast.Constant)
                                     and isinstance(node.body[0].value.value, str)) else node.body
            if _body_trivial(body):
                trivial += 1
                has_placeholder = True
            else:
                has_logic = has_logic or _has_logic(node)
    for n in tree.body:
        if isinstance(n, (ast.Assign, ast.AnnAssign, ast.Import, ast.ImportFrom, ast.ClassDef)):
            mod_logic = True
    if total == 0:
        return "MODULE_SHELL" if mod_logic else "EMPTY"
    if trivial == total and not has_logic:
        return "PLACEHOLDER"
    if has_placeholder and not has_logic:
        return "PLACEHOLDER"
    if has_placeholder and has_logic:
        return "SPARSE"
    return "REAL"


def main() -> None:
    stats: dict[str, Counter] = defaultdict(Counter)
    samples: dict[str, list[str]] = defaultdict(list)
    for rel in tracked_files():
        parts = rel.split("/")
        engine = parts[1] if len(parts) > 2 else "/"
        cat = classify(ROOT / rel)
        stats[engine][cat] += 1
        if cat in ("PLACEHOLDER", "SPARSE"):
            samples[engine].append(rel)
    width = max(len(k) for k in stats)
    keys = ["EMPTY", "MODULE_SHELL", "PLACEHOLDER", "SPARSE", "REAL", "BROKEN_SYNTAX"]
    print(f"{'ENGINE':<{width}} | " + " | ".join(k for k in keys) + " | TOTAL")
    agg = Counter()
    for engine in sorted(stats):
        c = stats[engine]
        agg.update(c)
        print(f"{engine:<{width}} | " + " | ".join(f"{c[k]:>4}" for k in keys) + f" | {sum(c.values())}")
    print(f"{'TOTAL':<{width}} | " + " | ".join(f"{agg[k]:>4}" for k in keys) + f" | {sum(agg.values())}")
    print("\n-- Weakest engines (placeholder+sparse share) --")
    for engine in sorted(stats):
        c = stats[engine]
        tot = sum(c.values())
        weak = c["PLACEHOLDER"] + c["SPARSE"]
        print(f"{engine:<{width}} {weak/tot*100:5.1f}% weak  ({weak}/{tot})")


if __name__ == "__main__":
    main()