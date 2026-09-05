"""Classify each repo under 06_SOURCE_CODE: real code vs stub vs empty vs broken.

A file is a STUB when it compiles but contains only a docstring + future import
or similar no-op. BROKEN means it fails to compile.
"""
import pathlib
import ast

ROOT = pathlib.Path(r"C:\Users\navid\Desktop\AURA\06_SOURCE_CODE")
SKIP = {"__pycache__", "node_modules", ".venv", "aura-memory", "aura-learning", "aura-brain"}
STUB_TOKENS = {"pass", "return True", "return {}", "return []", "TODO"}


def classify(text: str) -> str:
    try:
        tree = ast.parse(text)
    except SyntaxError:
        return "BROKEN"
    # count real statements beyond module docstring/imports
    body = [n for n in tree.body if not (isinstance(n, ast.Import) or isinstance(n, ast.ImportFrom))]
    assignments = 0
    classes = 0
    funcs = 0
    for node in body:
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            continue  # docstring
        if isinstance(node, ast.ClassDef):
            classes += 1
        elif isinstance(node, ast.FunctionDef):
            funcs += 1
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            assignments += 1
        else:
            assignments += 1
    if classes == 0 and funcs == 0 and assignments == 0:
        return "EMPTY"
    return "REAL" if classes + funcs + assignments >= 2 else "STUB"


for repo in sorted(p for p in ROOT.iterdir() if p.is_dir() and p.name not in SKIP):
    counts = {"REAL": 0, "STUB": 0, "EMPTY": 0, "BROKEN": 0}
    total = 0
    for p in repo.rglob("*.py"):
        if any(part in {"__pycache__", "node_modules", ".venv"} for part in p.parts):
            continue
        total += 1
        try:
            text = p.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        counts[classify(text)] += 1
    if total:
        print(f"{repo.name:<28} total={total:<5} real={counts['REAL']:<4} stub={counts['STUB']:<4} empty={counts['EMPTY']:<4} broken={counts['BROKEN']}")