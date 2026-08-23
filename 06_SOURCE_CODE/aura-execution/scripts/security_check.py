from pathlib import Path
text="".join(p.read_text(encoding="utf-8") for p in (Path(__file__).resolve().parents[1]/"aura_execution").rglob("*.py"))
assert "shell=True" not in text
print("security static checks passed")
