# Contributing

## Code of conduct

Be excellent to each other. See `CODE_OF_CONDUCT.md`.

## How to contribute

1. Open an issue describing the change and why it belongs in AURA.
2. Branch from `main`.
3. Implement against the **`06_SOURCE_CODE/aura`** package (the integrated
   platform). Do not add parallel engines that re-implement foundation,
   memory, reasoning, or security primitives the package already provides.
4. Add or update tests under `06_SOURCE_CODE/aura/tests/`.
5. Run the quality gates (see README) and fix every failure before opening the
   PR.
6. Update `CHANGELOG.md` and documentation for user-visible changes.

## Conventions

- One authoritative implementation per cross-cutting concern. Search the
  package before creating a new abstraction.
- Engines depend on foundation and security; they never reach into another
  engine's internals.
- Every public API accepts injected clocks/stores (no hidden global state).
- Safety-relevant behavior is default-deny and always explainable.
- Logs never contain secrets.

## Definition of done

- `ruff check` clean, `mypy` clean, `pytest` green.
- New behavior has tests that prove it (not smoke-only).
- Documents match reality: no marketing claims.
