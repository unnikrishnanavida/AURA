"""Core subpackage: domain models, errors, and the KnowledgeEngine.

Import concrete modules directly, e.g.::

    from aura_knowledge.core.models import Claim
    from aura_knowledge.core.engine import KnowledgeEngine
    from aura_knowledge.core.errors import ClaimNotFoundError

This ``__init__`` is intentionally minimal so importing ``aura_knowledge.core``
does not eagerly initialize the engine (which would create an import cycle).
"""