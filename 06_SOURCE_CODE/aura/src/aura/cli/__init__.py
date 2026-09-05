"""AURA command-line interface.

Useful developer/admin commands:
  aura doctor            environment and import diagnostics
  aura health            aggregate engine health
  aura ready             readiness probe
  aura config validate   validate configuration
  aura run               run a one-shot reasoning pass
  aura replay            replay a recorded execution
  aura security status   security posture summary
  aura audit             tail audit entries
  aura version           print version
"""

from __future__ import annotations

if __name__ == "__main__":
    from aura.cli.main import main

    raise SystemExit(main())

__all__ = ["main"]