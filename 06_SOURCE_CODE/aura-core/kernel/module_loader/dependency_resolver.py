from __future__ import annotations

from typing import Dict, List


class DependencyResolver:
    """Resolves simple dependency maps between modules."""

    def resolve(self, modules: Dict[str, List[str]]) -> List[str]:
        """Return an order of modules respecting dependencies using Kahn's algorithm."""
        # modules: name -> [dependencies]
        resolved: List[str] = []
        incoming = {k: set(v) for k, v in modules.items()}
        # reverse map
        dependents = {k: set() for k in modules}
        for mod, deps in modules.items():
            for d in deps:
                dependents.setdefault(d, set()).add(mod)

        independent = [m for m, deps in incoming.items() if not deps]
        while independent:
            n = independent.pop()
            resolved.append(n)
            for m in list(dependents.get(n, [])):
                incoming[m].discard(n)
                if not incoming[m]:
                    independent.append(m)
        if len(resolved) != len(modules):
            raise RuntimeError("Cyclic or missing dependencies detected")
        return resolved
