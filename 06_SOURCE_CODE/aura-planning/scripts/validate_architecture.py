from pathlib import Path
import ast, sys
def validate(root):
    errors=[]
    for path in Path(root).rglob("*.py"):
        try: ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError as exc: errors.append((str(path),str(exc)))
    return errors
if __name__=="__main__":
    errors=validate(sys.argv[1] if len(sys.argv)>1 else ".")
    print("\n".join(f"{p}: {e}" for p,e in errors))
    raise SystemExit(1 if errors else 0)
