"""Identifier utilities for aura-memory."""

import uuid


def new_id() -> str:
    return str(uuid.uuid4())


__all__ = ["new_id"]
