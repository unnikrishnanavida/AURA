from pathlib import Path
import ast, sys
def duplicates(root):
    found=[]
    for path in Path(root).rglob("*.py"):
        try: tree=ast.parse(path.read_text(encoding="utf-8"))
        except SyntaxError: continue
        for node in ast.walk(tree):
            if isinstance(node,(ast.Module,ast.ClassDef)):
                seen={}
                for child in node.body:
                    if isinstance(child,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef)):
                        seen.setdefault(child.name,[]).append(child.lineno)
                for name,lines in seen.items():
                    if len(lines)>1: found.append((str(path),name,lines))
    return found
if __name__=="__main__":
    found=duplicates(sys.argv[1] if len(sys.argv)>1 else ".")
    print("\n".join(map(str,found)))
    raise SystemExit(1 if found else 0)
