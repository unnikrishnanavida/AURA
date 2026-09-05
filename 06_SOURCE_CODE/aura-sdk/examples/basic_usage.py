"""End-to-end usage example for aura-sdk (deterministic local mode).

Run from the repository root with the canonical runtime importable:

    python 06_SOURCE_CODE/aura-sdk/examples/basic_usage.py

This example executes against the in-process canonical AURA runtime; it does
not fabricate network behavior.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "aura" / "src"))


def main() -> None:
    from aura_sdk import AuraSDK, SdkConfig
    from aura_sdk.config import TransportMode
    from aura_sdk.errors import SdkError

    print("== AURA SDK local-mode example ==")
    client = AuraSDK(config=SdkConfig(mode=TransportMode.LOCAL), seed=7)

    # observability
    print("health:", client.health()["status"])

    # memory
    mid = client.remember("example-note", {"text": "hello from the sdk"}, kind="episodic")
    print("memory id:", mid)
    print("recalled:", client.recall("example-note"))

    # knowledge
    cid = client.observe("the example ran successfully", predicate=("test",))
    print("claim id:", cid)

    # reasoning (uncertainty-first)
    answer = client.reason("did the example pass?", facts={"example_passed": 0.9})
    print("reasoning answer:", answer["answer"], "confidence:", answer["confidence"])

    # research
    research = client.research("Is the example valid?", claims=("the example ran successfully",))
    print("research findings:", len(research.get("findings", [])), "synthesis:", research.get("synthesis"))

    # metrics
    print("metrics keys:", list(client.metrics().get("counters", {}).keys())[:5])

    # typed errors
    try:
        client.execute("reason", {})
    except SdkError as exc:
        print("typed error:", exc.code, exc.message)


if __name__ == "__main__":
    main()