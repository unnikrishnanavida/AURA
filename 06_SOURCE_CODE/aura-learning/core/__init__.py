"""
AURA Learning - Core Package
============================

The ``core`` package provides the foundational infrastructure for the
AURA Learning repository. It contains reusable abstractions, contracts,
configuration primitives, runtime utilities, and shared base
components that are consumed by all higher-level learning modules.

Design Goals
------------
- Stable public API
- Zero learning-specific business logic
- Reusable infrastructure
- Strong typing
- Dependency inversion
- Enterprise-grade maintainability

This package intentionally avoids dependencies on higher-level
learning modules to prevent circular imports and preserve a clean
dependency graph.

Package Responsibilities
------------------------
* Base infrastructure
* Shared constants
* Exception hierarchy
* Common type aliases
* Configuration primitives
* Runtime lifecycle
* Dependency registration
* Repository abstractions
* Service abstractions
* Engine abstractions
* Health infrastructure

Author
------
AURA Development Team

License
-------
See LICENSE in the project root.
"""

from __future__ import annotations

# =============================================================================
# Package Metadata
# =============================================================================

__title__ = "aura-learning-core"
__description__ = "Core infrastructure for the AURA Learning framework."
__version__ = "1.0.0"
__author__ = "AURA Development Team"
__license__ = "MIT"

# =============================================================================
# Core Exports
# =============================================================================

from .constants import *
from .exceptions import *
from .types import *

# =============================================================================
# Public API
# =============================================================================

__all__: list[str] = [
    "__title__",
    "__description__",
    "__version__",
    "__author__",
    "__license__",
]

# =============================================================================
# Package Initialization
# =============================================================================

def package_information() -> dict[str, str]:
    """
    Return immutable package metadata.

    Returns
    -------
    dict[str, str]
        Metadata describing the package.
    """

    return {
        "title": __title__,
        "description": __description__,
        "version": __version__,
        "author": __author__,
        "license": __license__,
    }