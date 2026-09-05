"""Execution result response types for aura-execution."""

from __future__ import annotations


class StateTransitionError(Exception):
    """A transition between execution states is invalid for the state machine."""


__all__ = ["StateTransitionError"]