"""Output rendering for aura-cli.

Supports human-readable text and JSON output with stable shapes.
"""

from __future__ import annotations

import json
from typing import Any


def render_json(data: dict[str, Any]) -> str:
    return json.dumps(data, indent=2, sort_keys=True, default=str)


def render_text(header: str, lines: list[str]) -> str:
    parts = [header]
    if lines:
        parts.extend(f"  {line}" for line in lines)
    return "\n".join(parts)


def render_table(headers: list[str], rows: list[list[Any]]) -> str:
    if not rows:
        return "(no rows)"
    columns = headers
    widths = [len(str(c)) for c in columns]
    for row in rows:
        for i, cell in enumerate(row):
            widths[i] = max(widths[i], len(str(cell)))
    fmt = "  ".join(f"{{:<{w}}}" for w in widths)
    out = [fmt.format(*columns), "-" * sum(widths + [2 * (len(columns) - 1)])]
    for row in rows:
        padded = list(row) + [""] * (len(columns) - len(row))
        out.append(fmt.format(*[str(c)[: w] for c, w in zip(padded, widths)]))
    return "\n".join(out)


__all__ = ["render_json", "render_table", "render_text"]