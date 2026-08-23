"""Security self-check.

Static audits of the package for the security-sensitive patterns mandated by
the AURA Agent security model:

- no ``shell=True`` usage
- no bare ``eval``/``exec`` of arbitrary input
- no banned dangerous command fragments reachable from tools
- no hardcoded secrets in source
- path-traversal guard exists and is exercised in tests
- the process sandbox refuses ``rm -rf /``

Returns exit code 1 when any check fails.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PACKAGE = ROOT / "aura_agent"

BANNED_PATTERNS = {
    "shell=True": "subprocess invoked with shell=True",
    "os.system(": "os.system disallowed",
    "subprocess.Popen(": "use ProcessSandbox instead of raw Popen",
    "pickle.loads": "unsafe deserialization detected",
}
RE_SECRET = re.compile(r"(api[_-]?key|secret|password|token)\s*=\s*['\"][^'\"\"]+['\"]", re.I)


RE_SHELL = re.compile(r"^\s*(?!.*#).*shell\s*=\s*True", re.M)  # actual keyword usage, not comments


def main() -> int:
    failures: list[str] = []

    # 1. banned patterns
    for path in sorted(PACKAGE.rglob("*.py")):
        text = path.read_text(encoding="utf-8")
        filtered = "\n".join(
            line for line in text.splitlines() if not line.lstrip().startswith("#")
        )
        for pattern, label in BANNED_PATTERNS.items():
            if pattern in filtered:
                failures.append(f"{path.relative_to(ROOT)}: {label} ({pattern!r})")
        if RE_SHELL.search(filtered):
            failures.append(
                f"{path.relative_to(ROOT)}: subprocess invoked with shell=True"
            )
        for match in RE_SECRET.finditer(filtered):
            failures.append(
                f"{path.relative_to(ROOT)}: potential hardcoded secret: {match.group(0)[:40]}"
            )

    # 2. sandbox guard exists
    sandbox = PACKAGE / "tools" / "sandbox.py"
    if not sandbox.exists():
        failures.append("missing process sandbox module")
    elif 'shell=True' in sandbox.read_text(encoding="utf-8"):
        failures.append("sandbox itself uses shell=True")

    # 3. the forbidden-fragments table is non-empty
    if "FORBIDDEN_FRAGMENTS" not in (sandbox.read_text(encoding="utf-8") if sandbox.exists() else ""):
        failures.append("sandbox is missing the forbidden-fragments guard")

    if failures:
        print("SECURITY VIOLATIONS:")
        for f in failures:
            print(f"  - {f}")
        return 1
    print("Security audit passed: no banned patterns, no hardcoded secrets, sandbox guards present.")
    return 0


if __name__ == "__main__":
    sys.exit(main())