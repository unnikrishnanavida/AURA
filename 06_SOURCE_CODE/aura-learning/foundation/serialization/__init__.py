"""
==============================================================
AURA Framework

Foundation Serialization Package

Enterprise Serialization Foundation

Provides:

• Serialization Interfaces
• Models
• Validators
• Utilities
• Constants
• Exceptions
• Type System

==============================================================
"""

from __future__ import annotations

# ==========================================================
# Version
# ==========================================================

from .version import (
    VERSION,
    __version__,
)

# ==========================================================
# Constants
# ==========================================================

from .constants import *

# ==========================================================
# Exceptions
# ==========================================================

from .exceptions import *

# ==========================================================
# Types
# ==========================================================

from .types import *

# ==========================================================
# Interfaces
# ==========================================================

from .interfaces import *

# ==========================================================
# Models
# ==========================================================

from .models import *

# ==========================================================
# Utilities
# ==========================================================

from .utilities import *

# ==========================================================
# Validators
# ==========================================================

from .validators import *

# ==========================================================
# Package Information
# ==========================================================

PACKAGE_NAME = "foundation.serialization"

PACKAGE_DESCRIPTION = (
    "Enterprise serialization "
    "foundation package."
)

PACKAGE_AUTHOR = "AURA Framework"

# ==========================================================
# Runtime
# ==========================================================

def package_information() -> dict[str, str]:
    """
    Package information.
    """

    return {

        "name": PACKAGE_NAME,

        "description": PACKAGE_DESCRIPTION,

        "version": VERSION,

        "author": PACKAGE_AUTHOR,

    }


def package_version() -> str:
    """
    Package version.
    """

    return VERSION

# ==========================================================
# Public API
# ==========================================================

__all__ = [

    "VERSION",

    "__version__",

    "PACKAGE_NAME",

    "PACKAGE_DESCRIPTION",

    "PACKAGE_AUTHOR",

    "package_information",

    "package_version",

]