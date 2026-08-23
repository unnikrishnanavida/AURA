"""Shared fakes: a deterministic in-memory tool set for tests."""

from __future__ import annotations

import time
from typing import Any

from aura_agent.tools.models import SchemaField, Tool

__all__ = ["make_write_tool", "make_timeout_tool"]


def _write_handler(inputs: dict[str, Any], *, context) -> dict[str, Any]:
    if inputs["path"] == "/fail":
        raise RuntimeError("simulated tool failure")
    return {"written": inputs["path"], "ok": True}


def make_write_tool(*, timeout_s: float = 2.0) -> Tool:
    return Tool(
        name="filesystem.write",
        description="write content to a path",
        input_schema={
            "path": SchemaField(name="path", type=str, required=True),
            "content": SchemaField(name="content", type=str, required=True),
        },
        capability="filesystem.write",
        permissions=("filesystem:write",),
        handler=_write_handler,
        timeout_s=timeout_s,
    )


def make_timeout_tool(*, proc_time_s: float = 0.5, timeout_s: float = 0.1) -> Tool:
    def _handler(_inputs: dict[str, Any], *, context) -> dict[str, Any]:
        time.sleep(proc_time_s)
        return {"done": True}

    return Tool(
        name="tools.sleep",
        description="sleeps longer than its timeout",
        input_schema={},
        capability="tools.sleep",
        permissions=(),
        handler=_handler,
        timeout_s=timeout_s,
    )