import pathlib
import py_compile

roots = [
    pathlib.Path(r"c:\Users\navid\Desktop\AURA\06_SOURCE_CODE\aura-agents"),
    pathlib.Path(r"c:\Users\navid\Desktop\AURA\06_SOURCE_CODE\aura-sdk"),
]
for root in roots:
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