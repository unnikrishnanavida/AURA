"""AURA Mobile application package.

Consolidated from the previously shadowed ``aura_mobile/app.py`` module. The
attribute callers expect (``from aura_mobile.app import AuraMobileCore``) is now
provided by this package __init__; the module file was removed to eliminate the
file-vs-package shadowing conflict.
"""
from __future__ import annotations

from ..permissions.broker import PermissionBroker
from ..sync.queue import SyncQueue


class AuraMobileCore:
    """Mobile client core with default-deny permission broker."""

    def __init__(self, permissions=()):
        self.permissions = PermissionBroker(permissions)
        self.queue = SyncQueue()

    def request_capability(self, capability):
        self.permissions.require(capability)
        return True


__all__ = ["AuraMobileCore"]
