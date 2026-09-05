"""Causal strategy: influence propagation over a causal graph.

Rules read as causal edges: conditions jointly cause the consequent with the
rule's weight. Influence propagates from observed nodes.
"""

from __future__ import annotations

from collections import deque

from aura.reasoning.models import ReasoningInput, make_conclusion


class CausalStrategy:
    name = "causal"

    def reason(self, inp: ReasoningInput) -> object:
        graph: dict[str, list[tuple[str, float, str]]] = {}
        for rule in inp.rules:
            for condition in rule.conditions:
                graph.setdefault(condition, []).append((rule.consequent, rule.weight, rule.id))

        start_nodes = [p for p, v in inp.facts.items() if v >= 0.5]
        confidence: dict[str, float] = {node: inp.facts[node] for node in start_nodes}
        previous: dict[str, tuple[str, str]] = {}
        queue: deque[str] = deque(start_nodes)
        while queue:
            node = queue.popleft()
            for next_node, weight, rule_id in graph.get(node, []):
                candidate = confidence[node] * weight
                if next_node not in confidence or candidate > confidence[next_node]:
                    confidence[next_node] = candidate
                    previous[next_node] = (node, rule_id)
                    queue.append(next_node)

        if inp.question not in confidence:
            return make_conclusion(
                strategy=self.name,
                statement=f"UNKNOWN: no causal path from observations to {inp.question!r}",
                confidence=0.0,
                reasoning=["no causal chain connects observed facts to the question"],
            )

        path: list[str] = []
        reasons: list[str] = []
        node = inp.question
        while node in previous:
            parent, rule_id = previous[node]
            path.append(node)
            reasons.append(f"{parent} -> {node} via {rule_id}")
            node = parent
        path.append(node)
        path.reverse()

        return make_conclusion(
            strategy=self.name,
            statement=inp.question,
            confidence=confidence[inp.question],
            reasoning=[*reversed(reasons), f"causal path: {' -> '.join(path)}"],
            supports=[rid for _p, rid in previous.values()],
        )


__all__ = ["CausalStrategy"]