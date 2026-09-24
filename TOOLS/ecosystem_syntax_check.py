"""Ecosystem-wide syntax validation: compile every .py under 06_SOURCE_CODE (excluding heavy/generated trees)."""
import pathlib

ROOT = pathlib.Path(r"E:\AURA\06_SOURCE_CODE")
SKIP = {"__pycache__", "node_modules", ".venv", "aura-memory", "aura-learning", "aura-brain"}
# those three were already audited and are documented as historical scaffolds

import py_compile

results = {"ok": 0, "fail": []}
count = 0
for p in ROOT.rglob("*.py"):
    if any(part in SKIP for part in p.parts):
        continue
    count += 1
    try:
        py_compile.compile(str(p), doraise=True, cfile=str(p) + "c")
        results["ok"] += 1
    except Exception as exc:  # noqa: BLE001 - report every failure
        results["fail"].append((str(p), str(exc).splitlines()[0]))

print(f"scanned {count} files, {results['ok']} OK, {len(results['fail'])} failures")
for path, err in results["fail"][:60]:
    print(f"  FAIL {path}: {err}")
print(f"... total failures: {len(results['fail'])}")