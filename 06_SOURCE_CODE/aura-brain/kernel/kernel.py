"""
AURA Kernel

Public API exposed to the entire platform.
"""

from __future__ import annotations

from .engine import KernelEngine


class Kernel:
    """Main kernel interface."""

    def __init__(self):

        self._engine = KernelEngine()

    def start(self):

        self._engine.start()

    def shutdown(self):

        self._engine.shutdown()

    def restart(self):

        self._engine.restart()

    def status(self):

        return self._engine.status()

    @property
    def version(self):

        return self._engine.version()

    @property
    def context(self):

        return self._engine.context

    @property
    def container(self):

        return self._engine.container