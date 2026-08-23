"""AURA Agent public API.

This is the *documented, stable* public surface. Application code and examples
should import from here (or from :mod:`aura_agent.dsl`) rather than reaching
into internal engine modules.

Stable surface:
- :class:`~aura_agent.dsl.AgentBuilder` and :func:`~aura_agent.dsl.default_agent`
- execution pipeline types (:class:`ExecutionRequest`, :class:`ExecutionResult`)
- goal types (:class:`Goal`, :class:`GoalEngine`)
- policy/safety/autonomy types
- bridges (reasoning, planning, memory)
- telemetry + configuration
"""

from aura_agent._version import __version__
from aura_agent.dsl import AgentBuilder, default_agent

__all__ = ["__version__", "AgentBuilder", "default_agent"]