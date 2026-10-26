"""Top-level package for aura-core."""

# The core infrastructure packages (config, filesystem, security, ...) are
# regular packages that live alongside the aura_core package. They are
# exposed through the aura_core namespace so the codebase can import them as
# ``aura_core.<name>``.
import os
import sys

try:
    _CURRENT_PATH = sys.modules[__name__].__path__
except KeyError:  # pragma: no cover - defensive; import machinery always sets it
    _CURRENT_PATH = None

if _CURRENT_PATH is not None:
    _HERE = os.path.dirname(os.path.dirname(__file__))
    for _package in ("authorized_coding", "config", "filesystem", "security"):
        _candidate = os.path.join(_HERE, _package)
        if os.path.isdir(_candidate) and _candidate not in _CURRENT_PATH:
            _CURRENT_PATH.append(_candidate)

