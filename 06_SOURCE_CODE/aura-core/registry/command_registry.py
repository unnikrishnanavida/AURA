from __future__ import annotations

class CommandRegistry:
    def __init__(self) -> None:
        self._commands = {}

    def register(self, name: str, fn):
        self._commands[name] = fn

    def get(self, name: str):
        return self._commands.get(name)
