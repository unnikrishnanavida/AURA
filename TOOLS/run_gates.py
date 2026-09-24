import importlib.util
import os
import subprocess
import sys

ROOT = r"E:\AURA"
SRC = os.path.join(ROOT, "06_SOURCE_CODE", "aura", "src")
TESTS = os.path.join(ROOT, "06_SOURCE_CODE", "aura", "tests")
OUT = os.path.join(ROOT, "gates_output.txt")

lines = []
lines.append("python=%s" % sys.executable)
lines.append("prefix=%s" % sys.prefix)
lines.append("ruff=%s" % bool(importlib.util.find_spec("ruff")))
lines.append("mypy=%s" % bool(importlib.util.find_spec("mypy")))

if importlib.util.find_spec("ruff"):
    r = subprocess.run(
        [sys.executable, "-m", "ruff", "check", SRC, TESTS],
        capture_output=True, text=True, timeout=300,
    )
    lines.append("RUFF_EXIT=%d" % r.returncode)
    lines.append("RUFF_OUT=%s" % (r.stdout + r.stderr)[-6000:])

if importlib.util.find_spec("mypy"):
    m = subprocess.run(
        [sys.executable, "-m", "mypy", SRC, "--non-interactive"],
        capture_output=True, text=True, timeout=300,
    )
    lines.append("MYPY_EXIT=%d" % m.returncode)
    lines.append("MYPY_OUT=%s" % (m.stdout + m.stderr)[-6000:])

with open(OUT, "w", encoding="utf-8") as f:
    f.write("\n".join(lines))
print("WROTE", OUT)