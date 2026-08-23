import ast
from pathlib import Path
root=Path(__file__).resolve().parents[1]/"aura_execution"
for p in root.rglob("*.py"):
    ast.parse(p.read_text(encoding="utf-8"))
print("dependency syntax check passed")
