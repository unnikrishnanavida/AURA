"""Behavioral tests for the aura-core Kernel lifecycle orchestrator."""

from __future__ import annotations

import sys
from pathlib import Path

# aura-core is a flat-layout repo: import from repo root.
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from aura_core import __version__
from kernel.kernel import Kernel
from kernel.kernel_state import KernelState


class _BootHook:
    def __init__(self) -> None:
        self.calls = 0

    def run(self, kernel: Kernel) -> None:
        self.calls += 1


class _StartupHook:
    def __init__(self) -> None:
        self.calls = 0

    def run(self, kernel: Kernel) -> None:
        self.calls += 1


class _ShutdownHook:
    def __init__(self) -> None:
        self.calls = 0

    def run(self, kernel: Kernel) -> None:
        self.calls += 1


def test_version() -> None:
    assert isinstance(__version__, str)
    assert __version__


def test_kernel_initial_state() -> None:
    k = Kernel(name="t")
    assert k.state is KernelState.INITIALIZED


def test_start_transitions_to_running() -> None:
    k = Kernel()
    boot, startup = _BootHook(), _StartupHook()
    k.register("boot", boot)
    k.register("startup", startup)
    k.start()
    assert k.state is KernelState.RUNNING
    assert boot.calls == 1
    assert startup.calls == 1


def test_shutdown_runs_hooks_and_stops() -> None:
    k = Kernel()
    shutdown = _ShutdownHook()
    k.register("shutdown", shutdown)
    k.start()
    k.stop()
    assert k.state is KernelState.STOPPED
    assert shutdown.calls == 1


def test_start_on_running_is_noop() -> None:
    k = Kernel()
    k.start()
    k.start()  # second start must not crash or re-run boot
    assert k.state is KernelState.RUNNING


def test_register_resolve_roundtrip() -> None:
    k = Kernel()
    k.register("db", object())
    assert k.resolve("db") is not None
    assert k.resolve("missing") is None