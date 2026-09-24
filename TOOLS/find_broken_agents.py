"""Find Python files under the AURA source dirs that fail to compile.

Project-root discovery: this module lives at <project_root>/TOOLS/find_broken_agents.py,
so the project root is two directories above this file. Resolving everything relative to
__file__ (rather than hard-coding a drive path) keeps the tool working no matter where the
AURA working tree lives (e.g. E:\\AURA after the C: -> E: storage migration).
"""
import pathlib
import py_compile

PROJECT_ROOT = pathlib.Path(__file__).resolve().parent.parent

roots = [
    PROJECT_ROOT / "06_SOURCE_CODE" / "aura-agents",
    PROJECT_ROOT / "06_SOURCE_CODE" / "aura-sdk",
]
for root in roots:
    if not root.is_dir():
        print(f"== {root.name}: SKIPPED (missing: {root}) ==")
        continue
    fails = []
    for p in root.rglob("*.py"):
        if "__pycache__" in p.parts:
            continue
        try:
            py_compile.compile(str(p), doraise=True, cfile=str(p) + "c")
        except Exception as exc:
            fails.append((str(p), str(exc).splitlines()[0]))
    print(f"== {root.name}: {len(fails)} broken ==")
    for path, err in fails:
        print("  ", path)
        print("     ", err)