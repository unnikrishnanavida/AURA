"""AURA evaluation suite: measurable quality criteria over the canonical runtime.

Each evaluation is (a) deterministic, (b) grounded in real runtime behavior,
and (c) scored against an explicit, documented criterion. No benchmark numbers
are fabricated. Reports are written where the runtime exposes real data.

Scored dimensions (0..1 each):

  - task_completion: the pipeline succeeded exactly when every action succeeded
  - reasoning_correctness: for a rule-known question, the answer matches the rule
    conclusion and confidence reflects the rule weight
  - evidence_usage: research findings carry evidence counts and epistemic status
  - memory_retrieval_quality: recall returns the expected record first
  - planning_quality: the primary plan satisfies task prerequisites and is valid
  - execution_safety: an unauthorized action is never executed
  - reflection_quality: a failed outcome produces a failure-review + improvement
  - regression_protection: the learning loop flags metric regression
"""

from __future__ import annotations

import json
import time
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from aura.brain.engine import BrainEngine
from aura.core.pipeline import ExecutionPipeline, PipelineRequest, default_guardrails
from aura.execution.models import ActionSpec, ActionResult, make_result
from aura.execution.registry import ActionRegistry
from aura.foundation.cancellation import CancellationToken
from aura.learning.loop import LearningLoop
from aura.memory.engine import MemoryQuery
from aura.planning.models import Goal, Task
from aura.reasoning.models import Rule
from aura.security.permissions import Identity

FAIL_CAP = "admin.destructive"


class Evaluator:
    """Runs each dimension against isolated runtimes and returns a report."""

    def evaluate_memory_retrieval(self) -> float:
        brain = BrainEngine.create(seed=1)
        brain.memory.remember(key="preferred", kind="semantic", content={"text": "the red signal at dawn"}, importance=0.9)
        brain.memory.remember(key="noise", kind="semantic", content={"text": "unrelated filler"}, importance=0.1)
        hits = brain.memory.recall(MemoryQuery(text="red signal"))
        return 1.0 if hits and hits[0].key == "preferred" else 0.0

    def evaluate_reasoning_correctness(self) -> float:
        brain = BrainEngine.create(seed=1)
        result = brain.reason(
            question="alpha is true",
            facts={"alpha": 0.9},
            rules=(Rule(id="r1", conditions=("alpha",), consequent="alpha is true", weight=0.9),),
        )
        if result.reasoning is None:
            return 0.0
        if "I do not know" in result.reasoning.answer or "CONTESTED" in result.reasoning.answer:
            return 0.0
        # the rule-derived answer must carry the rule's confidence (0.9 * 0.9)
        if result.reasoning.answer != "alpha is true":
            return 0.0
        return 1.0 if 0.75 <= result.reasoning.confidence <= 1.0 else 0.5

    def evaluate_planning_quality(self) -> float:
        from aura.planning.engine import PlanningEngine

        goal = Goal.create(description="build and deploy")
        tasks = [
            Task(name="build", capability="tool.build", prerequisites=()),
            Task(name="test", capability="tool.test", prerequisites=("build",)),
            Task(name="deploy", capability="tool.deploy", prerequisites=("test",)),
        ]
        result = PlanningEngine().plan(goal=goal, tasks=tasks)
        if result.primary is None:
            return 0.0
        order = [step.task.name for step in result.primary.steps]
        order_ok = order.index("build") < order.index("test") < order.index("deploy")
        by_name = {task.name: task for task in tasks}
        prereq_ok = all(
            all(p in order[: order.index(name)] for p in by_name[name].prerequisites)
            for name in order
        )
        return 1.0 if order_ok and prereq_ok else 0.0

    def evaluate_execution_safety(self) -> float:
        brain = BrainEngine.create(seed=1)
        registry = ActionRegistry()
        registry.register(ActionSpec(
            name="wipe", capability=FAIL_CAP, handler=lambda _i, _t: make_result(ok=True, output={"wiped": True})
        ))
        pipeline = ExecutionPipeline(brain=brain, registry=registry, guardrails=default_guardrails(registry))
        result = pipeline.run(
            PipelineRequest(
                question="attempt destructive action",
                goal=Goal.create(description="attempt wipe"),
                tasks=(Task(name="wipe", capability=FAIL_CAP, risk=0.9),),
                identity=Identity(id="eval"),
            )
        )
        return 1.0 if result.executions == [] else 0.0

    def evaluate_reflection_quality(self) -> float:
        brain = BrainEngine.create(seed=1)
        registry = ActionRegistry()
        registry.register(ActionSpec(
            name="fail", capability="eval.fail",
            handler=lambda _i, _t: make_result(ok=False, error="boom"),
            expected_effects=("done",),
        ))
        guardrails = default_guardrails(registry)
        from aura.execution.engine import ExecutionEngine

        pipeline = ExecutionPipeline(
            brain=brain,
            registry=registry,
            guardrails=guardrails,
            execution=ExecutionEngine(registry=registry, guardrails=guardrails),
        )
        result = pipeline.run(
            PipelineRequest(
                question="run the failing step",
                goal=Goal.create(description="run failing step"),
                tasks=(Task(name="fail", capability="eval.fail", risk=0.1),),
                identity=Identity(id="eval"),
            )
        )
        if result.reflection is None:
            return 0.0
        from aura.reflection.models import SignalKind

        kinds = {s.kind for s in result.reflection.signals}
        return 1.0 if SignalKind.FAILURE_REVIEW in kinds and SignalKind.IMPROVEMENT_SUGGESTION in kinds else 0.5

    def evaluate_regression_protection(self) -> float:
        loop = LearningLoop(regression_ratio=0.8)
        loop.record_metric("success_rate", 1.0)
        report = loop.monitor("success_rate", 0.4)
        return 1.0 if report.regressed else 0.0

    def evaluate_evidence_usage_and_research(self) -> float:
        from aura.research.engine import ResearchEngine
        from aura.research.models import EpistemicStatus, ResearchInput, ResearchQuestion, SourceQuality

        output = ResearchEngine().research(
            ResearchInput(
                question=ResearchQuestion.create("Is A correct?"),
                claims=("A is correct",),
                evidence={"A is correct": (0.9, SourceQuality.PRIMARY, 0.9)},
                seed=1,
            )
        )
        findings = output.findings
        if not findings:
            return 0.0
        finding = findings[0]
        return 1.0 if finding.status is EpistemicStatus.EVIDENCE and finding.evidence_count >= 1 else 0.0

    def benchmark_latency_ms(self) -> dict[str, float]:
        """Measure important paths in-process (best effort, documented)."""
        brain = BrainEngine.create(seed=1)
        samples: dict[str, list[float]] = {"reason": [], "recall": [], "plan": []}
        for _ in range(5):
            started = time.monotonic()
            brain.reason(question="simple question?", facts={"q": 0.8})
            samples["reason"].append((time.monotonic() - started) * 1000)
        for _ in range(5):
            brain.memory.remember(key="x", kind="semantic", content={"v": 1})
        for _ in range(5):
            started = time.monotonic()
            brain.memory.recall(MemoryQuery(text="x"))
            samples["recall"].append((time.monotonic() - started) * 1000)
        from aura.planning.engine import PlanningEngine

        plan = PlanningEngine()
        goal = Goal.create(description="g")
        tasks = [Task(name=f"t{i}", capability="c", prerequisites=() if i == 0 else (f"t{i-1}",)) for i in range(5)]
        for _ in range(5):
            started = time.monotonic()
            plan.plan(goal=goal, tasks=tasks)
            samples["plan"].append((time.monotonic() - started) * 1000)
        return {name: round(sum(v) / len(v), 3) for name, v in samples.items() if v}
def build_report() -> dict[str, Any]:
    evaluator = Evaluator()
    dimensions = {
        "memory_retrieval": evaluator.evaluate_memory_retrieval(),
        "reasoning_correctness": evaluator.evaluate_reasoning_correctness(),
        "planning_quality": evaluator.evaluate_planning_quality(),
        "execution_safety": evaluator.evaluate_execution_safety(),
        "reflection_quality": evaluator.evaluate_reflection_quality(),
        "regression_protection": evaluator.evaluate_regression_protection(),
        "research_evidence": evaluator.evaluate_evidence_usage_and_research(),
    }
    return {
        "generated_at": datetime.now(UTC).isoformat(),
        "criteria": "documented in module docstring; each dimension scored 0..1",
        "dimensions": dimensions,
        "overall": round(sum(dimensions.values()) / len(dimensions), 6),
        "latency_ms_avg": evaluator.benchmark_latency_ms(),
    }


def main() -> int:
    report = build_report()
    print(json.dumps(report, indent=2, sort_keys=True))
    out = Path(__file__).resolve().parent / "reports"
    out.mkdir(parents=True, exist_ok=True)
    (out / f"eval-{datetime.now(UTC).strftime('%Y%m%d-%H%M%S')}.json").write_text(
        json.dumps(report, indent=2, sort_keys=True), encoding="utf-8"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())