from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from aura_execution.models import Action
from aura_execution.runtime.dry_run import dry_run

result = dry_run([Action("a", "demo")])
print(result)
