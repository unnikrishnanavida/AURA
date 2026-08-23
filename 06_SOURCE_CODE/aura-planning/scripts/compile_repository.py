from pathlib import Path
import py_compile, sys
def compile_repository(root):
    errors=[]
    for path in Path(root).rglob("*.py"):
        try: py_compile.compile(str(path),doraise=True)
        except py_compile.PyCompileError as exc: errors.append((str(path),str(exc)))
    return errors
if __name__=="__main__":
    errors=compile_repository(sys.argv[1] if len(sys.argv)>1 else ".")
    print("\n".join(f"{p}: {e}" for p,e in errors))
    raise SystemExit(1 if errors else 0)
