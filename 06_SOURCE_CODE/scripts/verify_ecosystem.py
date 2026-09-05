"""Run the AURA ecosystem verification across every supported repository.

Usage (from the repository root):

    python 06_SOURCE_CODE/scripts/verify_ecosystem.py

This is the shared "release gate" script for Phases 5–8: it runs the canonical
suite (pytest + mypy + ruff), the SDK suite, the web suite (vitest + build +
lint), agents, the Phase 1–4 standalone repos, and the final integration test.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]  # 06_SOURCE_CODE
REPO_ROOT = ROOT.parent
VENV_PYTHON = REPO_ROOT / ".venv" / "Scripts" / "python.exe"

REPOS_WITH_TESTS = [
    "aura-core",
    "aura-cloud",
    "aura-research",
    "aura-security",
    "aura-desktop",
    "aura-mobile",
    "aura-execution-complete",
    "aura-agents",
    "aura-knowledge",
    "aura-planning",
    "aura-reflection",
    "aura-execution",
    "aura-api",
    "aura-cli",
    "aura-sdk",
]

STEPS: list[tuple[str, list[str], str]] = []


def run(step: str, cwd: Path, cmd: list[str]) -> bool:
    print(f"\n=== {step} ===")
    try:
        completed = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=600)
    except subprocess.TimeoutExpired:
        print(f"TIMEOUT {step}")
        return False
    tail = "\n".join(completed.stdout.splitlines()[-8:])
    if completed.returncode != 0:
        print(tail)
        print(completed.stderr.splitlines()[-6:] if completed.stderr else "")
        print(f"FAILED {step}")
        return False
    print(tail)
    print(f"OK {step}")
    return True


def main() -> int:
    import platform

    python = str(VENV_PYTHON) if VENV_PYTHON.exists() else sys.executable
    code_root = ROOT

    results: list[tuple[str, bool]] = []

    # 1. canonical runtime
    results.append((
        "canonical aura tests",
        run("aura tests", code_root / "aura", [str(python), "-m", "pytest", "tests/", "-q", "--no-header"]),
    ))
    results.append((
        "canonical mypy",
        run("aura mypy", code_root / "aura", [str(python), "-m", "mypy", "src/aura"]),
    ))
    results.append((
        "canonical ruff",
        run("aura ruff", code_root / "aura", [str(python), "-m", "ruff", "check", "src/aura", "tests"]),
    ))

    # 2. SDK + integration
    results.append((
        "aura-sdk tests",
        run("aura-sdk tests", code_root / "aura-sdk", [str(python), "-m", "pytest", "tests/", "-q", "--no-header"]),
    ))
    results.append((
        "aura-sdk ruff",
        run("aura-sdk ruff", code_root / "aura-sdk", [str(python), "-m", "ruff", "check", "aura_sdk", "tests"]),
    ))

    # 3. web (build + lint + test)
    npm = "npm.cmd" if platform.system() == "Windows" else "npm"
    results.append(("aura-web build", run("aura-web build", code_root / "aura-web", [npm, "run", "build"])))
    results.append(("aura-web lint", run("aura-web lint", code_root / "aura-web", [npm, "run", "lint"])))
    results.append(("aura-web test", run("aura-web test", code_root / "aura-web", [npm, "test"])))

    # 4. standalone repos
    for repo in REPOS_WITH_TESTS:
        tests = code_root / repo / "tests"
        if not tests.exists():
            continue
        results.append((
            f"{repo} tests",
            run(f"{repo} tests", code_root / repo, [str(python), "-m", "pytest", "tests/", "-q", "--no-header"]),
        ))

    # 5. cross-repo integration + evaluation
    results.append((
        "final integration",
        run("final integration", code_root, [str(python), "-m", "pytest", "tests/test_final_integration.py", "-q", "--no-header"]),
    ))
    results.append((
        "evaluation suite",
        run("evaluation suite", code_root, [str(python), "evaluation/evaluate.py"]),
    ))

    passed = sum(1 for _name, ok in results if ok)
    print(f"\n{'=' * 60}")
    print(f"VERIFICATION {'PASSED' if passed == len(results) else 'FAILED'}: {passed}/{len(results)}")
    for name, ok in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())