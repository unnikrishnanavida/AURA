"""Deployment configuration validation.

Part of the startup gate: validates that a given environment/configuration
combination is deployable *before* the API server binds a port. This is the
explicit "fail clearly on invalid production configuration" path; engines never
silently downgrade a production config to a dev default.

Exit codes:
  0  configuration is valid for the requested environment
  1  configuration is invalid (message printed to stdout)
  2  usage error
"""

from __future__ import annotations

import os
import sys


def validate_deployment(environment: str, *, storage_backend: str | None = None) -> str:
    """Return an error message when the deployment configuration is unsafe.

    Returns an empty string when the configuration passes.
    """
    from aura.config.loader import ConfigLoader
    from aura.config.settings import Environments

    try:
        env_enum = Environments(environment)
    except ValueError:
        return f"unknown environment {environment!r}"

    overrides: dict[str, object] = {"environment": environment}
    if storage_backend is not None:
        overrides["storage"] = {"backend": storage_backend}
    try:
        config = ConfigLoader().load(overrides=overrides)
    except Exception as exc:  # pydantic/ConfigurationError
        return f"configuration rejected: {str(exc).splitlines()[0]}"

    if env_enum is Environments.PRODUCTION:
        if config.storage.backend == "memory":
            return "production requires storage.backend = 'sqlite' or 'postgresql' (memory rejected)"
        if not os.environ.get("AURA_API_SECRET") or len(os.environ["AURA_API_SECRET"]) < 16:
            return "production requires AURA_API_SECRET of at least 16 characters"
    return ""


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) < 1:
        print("usage: validate_deployment.py <environment> [--storage=sqlite]", file=sys.stderr)
        return 2
    environment = args[0]
    storage_backend: str | None = None
    for flag in args[1:]:
        if flag.startswith("--storage="):
            storage_backend = flag.split("=", 1)[1]
    error = validate_deployment(environment, storage_backend=storage_backend)
    if error:
        print(f"DEPLOYMENT CONFIG INVALID: {error}", file=sys.stderr)
        return 1
    print(f"deployment configuration valid for environment {environment!r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())