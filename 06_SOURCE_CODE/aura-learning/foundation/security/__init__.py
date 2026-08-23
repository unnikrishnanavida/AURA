"""
==============================================================
AURA Framework

Foundation Security Package

Enterprise Security Foundation

Provides

• Exceptions
• Constants
• Types
• Interfaces
• Models
• Utilities
• Validators
• Version Information

Example

from aura.foundation.security import *

==============================================================
"""

from .exceptions import *
from .constants import *
from .types import *
from .interfaces import *
from .models import *
from .utilities import *
from .validators import *

from .version import (
    AUTHOR,
    BUILD,
    COMPONENT_NAME,
    FEATURE_FLAGS,
    FULL_VERSION,
    LICENSE,
    MAJOR,
    MAXIMUM_PYTHON,
    MINIMUM_PYTHON,
    MINOR,
    PACKAGE_NAME,
    PATCH,
    ReleaseStage,
    SecurityVersion,
    STAGE,
    VERSION,
    feature_enabled,
    package_info,
    version_info,
)

# ==========================================================
# Public Version
# ==========================================================

__version__ = VERSION

# ==========================================================
# Package Metadata
# ==========================================================

__author__ = AUTHOR

__license__ = LICENSE

__package_name__ = PACKAGE_NAME

__component__ = COMPONENT_NAME

# ==========================================================
# Runtime Helpers
# ==========================================================

def package_summary() -> dict[str, object]:
    """
    Return Security package summary.
    """

    return {

        "package": PACKAGE_NAME,

        "component": COMPONENT_NAME,

        "version": VERSION,

        "full_version": FULL_VERSION,

        "stage": STAGE.value,

        "python": {

            "minimum": MINIMUM_PYTHON,

            "maximum": MAXIMUM_PYTHON,

        },

        "features": FEATURE_FLAGS.copy(),

    }


def runtime_information() -> SecurityVersion:
    """
    Runtime version information.
    """

    return version_info()


# ==========================================================
# Public API
# ==========================================================

__all__ = [

    # Version

    "VERSION",

    "FULL_VERSION",

    "SecurityVersion",

    "ReleaseStage",

    "version_info",

    "package_info",

    "feature_enabled",

    "package_summary",

    "runtime_information",

]