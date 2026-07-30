"""AURA SDK public client entrypoint."""

from dataclasses import dataclass

@dataclass
class AuraSDK:
    """Core SDK entrypoint for orchestrating AURA workflows."""
    name: str = "aura-sdk"

    def start(self) -> str:
        return "AURA SDK initialized"
