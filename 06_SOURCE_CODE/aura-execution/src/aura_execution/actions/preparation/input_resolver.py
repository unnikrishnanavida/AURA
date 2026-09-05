"""Resolve raw action inputs into the exact input set the handler expects."""

from __future__ import annotations

from typing import Any


def resolve_inputs(action: Any, inputs: dict[str, Any]) -> dict[str, Any]:
    """Merge declared action inputs (schema/defaults) with the request inputs.

    The action may declare an iterable of input names (``actions.inputs``) or
    a mapping of name -> default. Provided inputs override defaults; declared
    inputs missing from both become None so the handler has a stable shape.
    """
    declared = action.inputs or {}
    provided = dict(inputs)
    resolved: dict[str, Any] = {}
    if isinstance(declared, (set, frozenset, list, tuple)):
        for name in declared:
            resolved[name] = provided.get(name)
    elif isinstance(declared, dict):
        for name, default in declared.items():
            resolved[name] = provided.get(name, default)
    else:
        raise TypeError("action.inputs must be an iterable of names or a name->default mapping")
    resolved.update({k: v for k, v in provided.items() if k not in resolved})
    return resolved


__all__ = ["resolve_inputs"]