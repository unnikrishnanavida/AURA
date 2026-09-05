# Security

AURA Agent treats security as a first-class concern. This document describes
the security model and the controls in place.

## Security principles

1. **Default-deny.** The permission engine denies anything not explicitly
   allowed. The default `AgentBuilder` grants nothing.
2. **Bounded execution.** Tools run through a process sandbox that never
   spawns a real shell, enforces timeouts, and captures output. Known-dangerous
   command fragments are refused before execution.
3. **Non-bypassable safety.** Autonomy mode can relax approval gates but can
   never convert a safety `DENY`, a permission `DENY`, a constitution `DENY`,
   or an exhausted-budget into an execution.
4. **No hardcoded secrets.** Configuration comes from the environment; the
   logging layer redacts API keys, passwords, tokens, and credentials before
   emission.
5. **No unsafe deserialization.** There is no `pickle.loads` or arbitrary
   `eval`/`exec` in the package.
6. **Path-traversal guard.** The sandbox exposes `is_subpath()` for
   filesystem-bounded tools and the tool input schema rejects unknown keys.

## Audited patterns

`scripts/security_check.py` statically audits the package for:

- `subprocess` with a real shell (`shell=True` outside comments),
- `os.system`,
- raw `subprocess.Popen` bypassing the sandbox,
- `pickle.loads`,
- hardcoded secret-looking assignments.

A failing check exits non-zero and must be resolved before release.

## Known limitations

- The process sandbox uses `subprocess.run` with `capture_output=True` and a
  wall-clock timeout. It does **not** provide full OS-level isolation (no
  container/namespace separation); for hostile workloads, deploy inside a
  container.
- In-process tool handlers run in a thread pool with cooperative timeout; a
  handler that ignores `threading` interrupts is bounded by the process-level
  sandbox when run through `ProcessSandbox`.

## Reporting

Please report suspected vulnerabilities privately to the AURA maintainers with
an affected-version and reproducer; do not open a public issue for
security-sensitive findings.