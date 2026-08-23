"""AURA SDK package root.

This module imports the public `AuraSDK` entrypoint and performs
lightweight runtime augmentation of module stubs so managers and
validators across the package provide useful default behaviours.
"""
from .aura import AuraSDK

# Import runtime injector to add generic implementations to stub classes.
from . import _impl

__all__ = ["AuraSDK"]
