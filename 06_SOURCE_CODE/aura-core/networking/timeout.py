from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from aura_core.environment.os_compat import is_windows

if is_windows():
    from aura_core.compatibility.win_timeout import Timeout as _Timeout
else:
    from aura_core.compatibility.posix_timeout import Timeout as _Timeout


@contextmanager
def timeout(seconds: int) -> Iterator[None]:
    """Cross-platform timeout context manager.

    Usage:
        with timeout(5):
            do_something()
    """
    ctx = _Timeout(seconds)
    try:
        ctx.__enter__()
        yield
    finally:
        ctx.__exit__(None, None, None)
