"""Summarize npm audit findings."""

import json
from pathlib import Path

p = Path(__file__).resolve().parent / "npm-audit.json"
d = json.loads(p.read_text(encoding="utf-8"))
for f in d.get("findings", []):
    print(f"{f['package']} [{f['severity']}] fix={f['fix_available']}: via={f['via'][:150]}")