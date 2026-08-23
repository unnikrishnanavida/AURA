"""Tool registry: registration, lookup, and name enumeration."""

from __future__ import annotations

from aura_agent.tools.models import Tool

__all__ = ["ToolRegistry"]


class ToolRegistry:
    """Owns the set of registered tools.

    Tools are looked up by name and created elsewhere (the execution bridge /
    kernel bootstrap). The registry deliberately performs no logic other than
    registration and lookup; execution policy lives in the execution engine.
    """

    def __init__(self) -> None:
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> Tool:
        """Register a tool, replacing any same-named prior registration."""
        self._tools[tool.name] = tool
        return tool

    def unregister(self, name: str) -> None:
        self._tools.pop(name, None)

    def get(self, name: str) -> Tool | None:
        return self._tools.get(name)

    def has(self, name: str) -> bool:
        return name in self._tools

    def names(self) -> list[str]:
        return sorted(self._tools)

    def all(self) -> list[Tool]:
        return list(self._tools.values())

    def capabilities(self) -> dict[str, list[str]]:
        """Map capability names to the tools that provide them."""
        mapping: dict[str, list[str]] = {}
        for tool in self._tools.values():
            mapping.setdefault(tool.capability, []).append(tool.name)
        return mapping
