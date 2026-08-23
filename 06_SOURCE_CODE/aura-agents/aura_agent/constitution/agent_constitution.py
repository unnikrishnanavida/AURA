"""Agent constitution: the bounded, explicit rule set for agent behavior."""

from __future__ import annotations

from aura_agent.constitution.enforcement.constitution_checker import ConstitutionChecker
from aura_agent.constitution.principles.principle import Principle

__all__ = ["AgentConstitution"]


class AgentConstitution:
    """Owns the constitution's principles and its enforcement checker.

    The constitution is frozen at construction time by default; copying in
    additional principles at runtime is possible only through the explicit
    ``amend`` flow (which records provenance). Learning/reflection can never
    amend the constitution implicitly.
    """

    def __init__(self, principles: list[Principle] | None = None) -> None:
        self._principles: list[Principle] = list(principles or [])
        self.checker = ConstitutionChecker(self._principles)
        self._amendments: list[tuple[Principle, str]] = []

    def amend(self, principle: Principle, *, authorized_by: str) -> None:
        """Explicitly amend the constitution (requires an authorizing entity)."""
        if not authorized_by:
            raise ValueError("constitutional amendment requires an authorizing entity")
        self._principles.append(principle)
        self.checker.add_principle(principle)
        self._amendments.append((principle, authorized_by))

    @property
    def principles(self) -> list[Principle]:
        return list(self._principles)

    def check(self, action: str, capability: str):
        return self.checker.check(action, capability)