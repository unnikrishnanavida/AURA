"""Clean-environment installation verification (Phase 17).

Proves the AURA packages install and work in a *fresh* environment that has
never seen the repository's virtualenv, caches, editable installs, or locally
built artifacts.

What it does
------------
1. Builds wheels for ``aura`` and ``aura-sdk`` from source (removing any prior
   build/ artifacts first).
2. Creates a brand-new virtualenv under a temp directory.
3. Installs ONLY the built wheels (plus ``--find-links`` for test extras --
   declared dependencies are fetched normally from the index).
4. Runs import checks against the installed packages.
5. Optionally runs the packaged test suites against the fresh env.

Usage
-----
    python 06_SOURCE_CODE/evaluation/clean_install_test.py [--with-tests]

Exit code 0 = full success; otherwise a specific step failed.
"""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]  # 06_SOURCE_CODE
AURA_REPO = ROOT / "aura"
SDK_REPO = ROOT / "aura-sdk"
VENV_PYTHON = ROOT.parent / ".venv" / "Scripts" / "python.exe"

PACKAGES = (
    ("aura", AURA_REPO),
    ("aura-sdk", SDK_REPO),
)


def _run(cmd: list[str], cwd: Path, *, timeout: int = 600) -> subprocess.CompletedProcess:
    print(f"\n$ {' '.join(str(c) for c in cmd)}  (cwd={cwd})")
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout, env=_fresh_env())


def _check(step: str, result: subprocess.CompletedProcess) -> None:
    if result.returncode != 0:
        print(f"[FAIL] {step}")
        print(result.stdout[-2000:])
        print(result.stderr[-2000:])
        raise SystemExit(f"clean install verification failed at: {step}")


def _build_into(dist: Path) -> list[Path]:
    """Build wheels for all packages into ``dist`` after clearing stale artifacts."""
    if dist.exists():
        shutil.rmtree(dist)
    dist.mkdir(parents=True)
    wheels: list[Path] = []
    for name, repo in PACKAGES:
        for artifact in ("build", "dist"):
            leftover = repo / artifact
            if leftover.exists():
                shutil.rmtree(leftover)
        result = _run([str(python()), "-m", "build", "--wheel", "--outdir", str(dist)], repo)
        _check(f"build {name}", result)
        built = sorted(dist.glob(f"{name.replace('-', '_')}-*.whl"))
        if not built:
            raise SystemExit(f"no wheel produced for {name} in {dist}")
        wheels.append(built[-1])
        print(f"[ok] built {built[-1].name}")
    return wheels


def python() -> Path:
    return VENV_PYTHON if VENV_PYTHON.exists() else Path(sys.executable)


def _make_fresh_venv() -> tuple[Path, Path]:
    base = Path(tempfile.mkdtemp(prefix="aura-clean-"))
    venv = base / "venv"
    result = _run([str(python()), "-m", "venv", str(venv)], base)
    _check("create fresh venv", result)
    py = venv / "Scripts" / "python.exe" if os.name == "nt" else venv / "bin" / "python"
    return base, py


def _fresh_env() -> dict[str, str]:
    """Environment for fresh-venv subprocesses with infra-coupled vars cleared.

    The clean install must not inherit ``AURA_TEST_POSTGRESQL_DSN`` (or any
    other infra hint) from the invoking shell; otherwise PG-gated tests would
    try to run against a database the fresh venv has no driver for.
    """
    env = dict(os.environ)
    for key in ("AURA_TEST_POSTGRESQL_DSN", "AURA_STORAGE_POSTGRESQL_DSN", "AURA_API_DISTRIBUTED_STATE_DSN"):
        env.pop(key, None)
    return env


def _verify_imports(venv_py: Path) -> None:
    code = (
        "import importlib;"
        "import aura;"
        "from aura.sdk.client import Aura;"
        "import aura_sdk;"
        "from aura_sdk import AuraSDK;"
        "print('aura import ok', importlib.metadata.version('aura'));"
        "print('aura-sdk import ok', importlib.metadata.version('aura-sdk'))"
    )
    result = _run([str(venv_py), "-c", code], ROOT)
    _check("import checks", result)
    print(result.stdout.strip())


def _verify_runtime(venv_py: Path) -> None:
    """Instantiate the SDK in local mode against the fresh install."""
    code = (
        "from aura_sdk import AuraSDK, SdkConfig;"
        "from aura_sdk.config import TransportMode;"
        "sdk = AuraSDK(config=SdkConfig(mode=TransportMode.LOCAL));"
        "out = sdk.request('health');"
        "assert out.ok, out.to_dict();"
        "print('sdk local mode ok, operation:', out.operation)"
    )
    result = _run([str(venv_py), "-c", code], ROOT)
    _check("runtime smoke (SDK local mode)", result)
    print(result.stdout.strip())


def _run_packaged_tests(venv_py: Path) -> None:
    """Install dev extras into the fresh venv and run the canonical tests."""
    result = _run(
        [str(venv_py), "-m", "pip", "install", "-q", "pytest>=7", "ruff>=0.4", "cryptography>=42"],
        ROOT,
    )
    _check("install test deps into fresh venv", result)
    result = _run([str(venv_py), "-m", "pytest", "tests/", "-q", "--no-header"], AURA_REPO)
    _check("canonical test suite in fresh venv", result)
    tail = "\n".join(result.stdout.splitlines()[-3:])
    print(tail)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--with-tests", action="store_true", help="also run the test suite in the fresh venv")
    args = parser.parse_args()

    base_dir = Path(tempfile.mkdtemp(prefix="aura-clean-build-"))
    dist = base_dir / "wheels"
    try:
        wheels = _build_into(dist)
        env_dir, venv_py = _make_fresh_venv()
        install = [str(venv_py), "-m", "pip", "install", "--no-cache-dir"]
        install.extend(str(w) for w in wheels)
        result = _run(install, ROOT)
        if result.returncode != 0 and "ConnectionResetError" in (result.stderr or ""):
            # Transient PyPI network failure; retry once before declaring failure.
            print("[retry] transient network error while installing wheels")
            result = _run(install, ROOT)
        _check("install wheels into fresh venv", result)
        _verify_imports(venv_py)
        _verify_runtime(venv_py)
        if args.with_tests:
            _run_packaged_tests(venv_py)
    finally:
        shutil.rmtree(base_dir, ignore_errors=True)

    print("\nCLEAN INSTALL VERIFICATION: PASSED")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())