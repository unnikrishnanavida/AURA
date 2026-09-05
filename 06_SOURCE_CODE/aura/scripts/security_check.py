"""Static security scan gate.

Scans the source tree for high-risk patterns that should not reach
production: shell execution, untrusted deserialization, accidental secret
logging, and hardcoded credentials.

Run:  python scripts/security_check.py
"""

from __future__ import annotations

import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parents[1]
SCAN_DIRS = ((ROOT / "src"), (ROOT / "tests"))

HIGH_RISK = (
    (r"os\.system\s*\(", "os.system usage"),
    (r"subprocess\.(run|Popen|call|check_output)\s*\([^)]*shell\s*=\s*True", "shell=True subprocess"),
    (r"pickle\.(loads|load)\s*\(", "untrusted pickle deserialization"),
    (r"eval\s*\(", "eval on dynamic input"),
    (r"exec\s*\(", "exec on dynamic input"),
    (r"yaml\.load\s*\([^)]*Loader\s*=\s*yaml\.(FullLoader|UnsafeLoader|Loader)", "unsafe yaml loader"),
)

SECRET_PATTERNS = (
    (r"password\s*=\s*['\"][^'\"]+['\"]", "hardcoded password"),
    (r"api[_-]?key\s*=\s*['\"][^'\"]+['\"]", "hardcoded api key"),
    (r"secret\s*=\s*['\"][^'\"]{8,}['\"]", "hardcoded secret"),
    (r"BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY", "embedded private key"),
)


def scan() -> int:
    failures: list[str] = []
    for base in SCAN_DIRS:
        # Secret assignments are only scanned in src; tests legitimately use
        # dummy credentials, so scanning them would produce false positives.
        scan_secrets = base == (ROOT / "src")
        for path in sorted(base.rglob("*.py")):
            text = path.read_text(encoding="utf-8")
            for pattern, label in HIGH_RISK:
                if re.search(pattern, text):
                    failures.append(f"{path.relative_to(ROOT)}: {label}")
            if scan_secrets:
                for pattern, label in SECRET_PATTERNS:
                    for match in re.finditer(pattern, text):
                        # Ignore empty placeholders like  = ""
                        if match.group(0).rstrip("'\"").endswith("="):
                            continue
                        failures.append(f"{path.relative_to(ROOT)}: {label}: {match.group(0)}")

    if failures:
        print("SECURITY FAILURES:")
        for failure in failures:
            print(f"  {failure}")
        return 1
    print("security scan ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(scan())