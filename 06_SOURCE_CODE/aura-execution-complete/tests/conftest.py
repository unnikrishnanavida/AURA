"""Make the aura_execution package importable when running tests from source."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "src"))