"""Phase 35 local performance baseline (honest numbers, single machine).

Measures the canonical in-process reasoning path (deterministic vs with a
synthesis provider) and memory writes. LOCAL baseline only — not a production
load test; numbers are recorded in the acceptance report.
"""

from __future__ import annotations

import json
import time

from aura.brain.engine import BrainEngine
from aura.config.settings import AuraConfig
from aura.foundation.ids import MemoryId
from aura.memory.models import MemoryEntry, MemoryType
from aura.observability.metrics import Metrics
from aura.providers.base import Provider, ProviderProfile
from aura.providers.manager import ProviderManager
from aura.reasoning.models import Rule

SOCRATES = (Rule(id="r1", conditions=("socrates is human", "humans are mortal"), consequent="socrates is mortal"),)
FACTS = {"socrates is human": 1.0, "humans are mortal": 1.0}


class P35Provider(Provider):
    name = "p35"
    timeout_seconds = 10.0

    def __init__(self) -> None:
        self.calls = 0
        self.profile = ProviderProfile(
            name=self.name, kind="reasoning", capabilities=("reasoning.synthesis",), privacy_approved=True, local=True
        )

    def health(self) -> bool:
        return True

    def reason(self, question: str, **kwargs: object) -> object:
        self.calls += 1
        return "p35-ok"


def bench(fn, *, n: int, label: str) -> dict[str, float]:
    for _ in range(5):  # warm up
        fn()
    start = time.perf_counter()
    for _ in range(n):
        fn()
    elapsed = time.perf_counter() - start
    per_call_ms = elapsed * 1000.0 / n
    print(f"{label:38s} {n} calls  {elapsed:.2f}s  {per_call_ms:.3f} ms/call ({n / elapsed:.0f} ops/s)")
    return {"label": label, "calls": n, "elapsed_s": round(elapsed, 3), "ms_per_call": round(per_call_ms, 4)}


def main() -> int:
    deterministic = BrainEngine.create(config=AuraConfig(), seed=42)

    def reason_deterministic() -> None:
        deterministic.reason(question="socrates is mortal", facts=FACTS, rules=SOCRATES)

    provider = P35Provider()
    manager = ProviderManager(metrics=Metrics())
    manager.register(provider)
    with_provider = BrainEngine.create(config=AuraConfig(), seed=42, provider_manager=manager)

    def reason_with_provider() -> None:
        with_provider.reason(question="socrates is mortal", facts=FACTS, rules=SOCRATES)

    def memory_write() -> None:
        deterministic.memory.store.add(
            MemoryEntry(id=MemoryId.new(), key="bench", kind=MemoryType.SEMANTIC, content={"text": "x"})
        )

    results = [
        bench(reason_deterministic, n=200, label="reason deterministic (in-process)"),
        bench(reason_with_provider, n=200, label="reason with synthesis provider"),
        bench(memory_write, n=200, label="memory write (in-memory store)"),
    ]
    print(json.dumps({"results": results, "provider_calls": provider.calls}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())