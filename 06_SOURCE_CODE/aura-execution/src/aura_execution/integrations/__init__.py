"""Integration adapters from aura-execution to other AURA subsystems.

Boundary decision (documented):

- ``aura-execution`` (this package) is the AUTHORITATIVE execution runtime.
- ``aura-execution-complete`` is a legacy/HISTORICAL prototype. Both packages
  share the same top-level module name ``aura_execution``, so they cannot
  coexist in one interpreter and no in-process bridge can exist. Code that
  must run the legacy interface should run against that repo in isolation;
  the authoritative runtime is this package.
"""
