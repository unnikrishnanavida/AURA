from pathlib import Path
import ast,sys
root=Path(__file__).resolve().parents[1]/"aura_execution"
errors=[]
count=0
for p in root.rglob("*.py"):
    count+=1
    try:ast.parse(p.read_text(encoding="utf-8"))
    except Exception as e:errors.append((str(p),str(e)))
print(f"AST validated: {count} Python files")
if errors:
    for e in errors:print(*e,sep=": ")
    sys.exit(1)
