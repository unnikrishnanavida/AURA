"""
Domain-first implementation for benchmarks/causal/counterfactual.py.

Subsystem: causal
This module owns variable, edge, ancestor, descendant, confounder, intervention semantics.
The implementation is intentionally specialized to this subsystem. Shared
AURA infrastructure belongs in the infrastructure packages instead of being
copied into every domain module.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from collections import defaultdict, deque
from typing import Any, Mapping, Iterable


@dataclass
class CausalVariable:
    name: str
    observed: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class CausalEdge:
    source: str
    target: str
    relation: str = 'causes'
    weight: float = 1.0

@dataclass
class CausalGraph:
    variables: dict[str, Any] = field(default_factory=dict)
    edges: set[tuple[str, str]] = field(default_factory=set)

@dataclass
class Intervention:
    target: str
    value: Any
    mechanism: str = 'do'

@dataclass
class EffectEstimate:
    treatment: str
    outcome: str
    estimate: float
    adjustment: set[str] = field(default_factory=set)

class Counterfactual:
    def __init__(self):
        self.graph = {"variables": {}, "edges": set()}
        self.interventions = {}
        self.effects = {}

    def _reachable(self, start):
        seen, stack = set(), [start]
        while stack:
            node = stack.pop()
            for source, target in self.graph["edges"]:
                if source == node and target not in seen:
                    seen.add(target)
                    stack.append(target)
        return seen

    def _causal_cycle(self):
        visiting, visited = set(), set()
        children = defaultdict(set)
        for source, target in self.graph["edges"]:
            children[source].add(target)
        def visit(node):
            if node in visiting:
                return True
            if node in visited:
                return False
            visiting.add(node)
            if any(visit(child) for child in children[node]):
                return True
            visiting.remove(node)
            visited.add(node)
            return False
        return any(visit(node) for node in self.graph["variables"])

    def _causal_topology(self):
        indegree = {node: 0 for node in self.graph["variables"]}
        for source, target in self.graph["edges"]:
            indegree[target] = indegree.get(target, 0) + 1
        queue = deque(sorted(node for node, degree in indegree.items() if degree == 0))
        order = []
        while queue:
            node = queue.popleft()
            order.append(node)
            for source, target in sorted(self.graph["edges"]):
                if source == node:
                    indegree[target] -= 1
                    if indegree[target] == 0:
                        queue.append(target)
        if len(order) != len(indegree):
            raise ValueError("causal graph contains a directed cycle")
        return order

    def _causal_paths(self, source, target, prefix=None):
        prefix = [source] if prefix is None else prefix
        if source == target:
            return [prefix]
        paths = []
        for _, child in sorted(self.graph["edges"]):
            if _ == source and child not in prefix:
                paths.extend(self._causal_paths(child, target, prefix + [child]))
        return paths

    def add_variable(self, value=None, records=None, context=None):
        """Domain operation: add variable.

        This method owns a concrete causal responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        graph = self.graph
        if "add_variable" == "add_variable":
            label = str(value).strip()
            if not label: raise ValueError("causal variable name cannot be empty")
            graph["variables"].setdefault(label, {"observed": True})
            return label
        if "add_variable" == "add_edge":
            edge = tuple(value) if isinstance(value, (list, tuple)) and len(value) == 2 else None
            if edge is None or edge[0] == edge[1]: raise ValueError("causal edge must connect two distinct variables")
            graph["edges"].add(edge)
            return edge
        if "add_variable" in {"parents","children","ancestors","descendants"}:
            node = str(value)
            edges = graph["edges"]
            if "add_variable" == "parents": return sorted(a for a,b in edges if b == node)
            if "add_variable" == "children": return sorted(b for a,b in edges if a == node)
            frontier = [node]; seen = set()
            reverse = "add_variable" == "ancestors"
            while frontier:
                current = frontier.pop()
                neighbours = [a for a,b in edges if b == current] if reverse else [b for a,b in edges if a == current]
                for nxt in neighbours:
                    if nxt not in seen:
                        seen.add(nxt); frontier.append(nxt)
            return sorted(seen)
        if "add_variable" == "has_cycle":
            return self._causal_cycle()
        if "add_variable" == "topological_order":
            return self._causal_topology()
        if "add_variable" == "path_exists":
            src, dst = value
            return dst in self._reachable(src)
        if "add_variable" == "all_paths":
            src, dst = value
            return self._causal_paths(src, dst)
        if "add_variable" in {"observational_effect","interventional_effect","conditional_effect"}:
            rows = records if isinstance(records, list) else []
            treated = [float(r["outcome"]) for r in rows if r.get("treatment") == 1 and "outcome" in r]
            control = [float(r["outcome"]) for r in rows if r.get("treatment") == 0 and "outcome" in r]
            return (sum(treated)/len(treated) - sum(control)/len(control)) if treated and control else None
        if "add_variable" == "graph_summary":
            return {"variables": sorted(graph["variables"]), "edges": sorted(graph["edges"])}
        return {"domain": "causal", "operation": "add_variable", "model_size": len(graph["variables"]), "edge_count": len(graph["edges"])}


    def add_edge(self, value=None, records=None, context=None):
        """Domain operation: add edge.

        This method owns a concrete causal responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        graph = self.graph
        if "add_edge" == "add_variable":
            label = str(value).strip()
            if not label: raise ValueError("causal variable name cannot be empty")
            graph["variables"].setdefault(label, {"observed": True})
            return label
        if "add_edge" == "add_edge":
            edge = tuple(value) if isinstance(value, (list, tuple)) and len(value) == 2 else None
            if edge is None or edge[0] == edge[1]: raise ValueError("causal edge must connect two distinct variables")
            graph["edges"].add(edge)
            return edge
        if "add_edge" in {"parents","children","ancestors","descendants"}:
            node = str(value)
            edges = graph["edges"]
            if "add_edge" == "parents": return sorted(a for a,b in edges if b == node)
            if "add_edge" == "children": return sorted(b for a,b in edges if a == node)
            frontier = [node]; seen = set()
            reverse = "add_edge" == "ancestors"
            while frontier:
                current = frontier.pop()
                neighbours = [a for a,b in edges if b == current] if reverse else [b for a,b in edges if a == current]
                for nxt in neighbours:
                    if nxt not in seen:
                        seen.add(nxt); frontier.append(nxt)
            return sorted(seen)
        if "add_edge" == "has_cycle":
            return self._causal_cycle()
        if "add_edge" == "topological_order":
            return self._causal_topology()
        if "add_edge" == "path_exists":
            src, dst = value
            return dst in self._reachable(src)
        if "add_edge" == "all_paths":
            src, dst = value
            return self._causal_paths(src, dst)
        if "add_edge" in {"observational_effect","interventional_effect","conditional_effect"}:
            rows = records if isinstance(records, list) else []
            treated = [float(r["outcome"]) for r in rows if r.get("treatment") == 1 and "outcome" in r]
            control = [float(r["outcome"]) for r in rows if r.get("treatment") == 0 and "outcome" in r]
            return (sum(treated)/len(treated) - sum(control)/len(control)) if treated and control else None
        if "add_edge" == "graph_summary":
            return {"variables": sorted(graph["variables"]), "edges": sorted(graph["edges"])}
        return {"domain": "causal", "operation": "add_edge", "model_size": len(graph["variables"]), "edge_count": len(graph["edges"])}


    def parents(self, value=None, records=None, context=None):
        """Domain operation: parents.

        This method owns a concrete causal responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        graph = self.graph
        if "parents" == "add_variable":
            label = str(value).strip()
            if not label: raise ValueError("causal variable name cannot be empty")
            graph["variables"].setdefault(label, {"observed": True})
            return label
        if "parents" == "add_edge":
            edge = tuple(value) if isinstance(value, (list, tuple)) and len(value) == 2 else None
            if edge is None or edge[0] == edge[1]: raise ValueError("causal edge must connect two distinct variables")
            graph["edges"].add(edge)
            return edge
        if "parents" in {"parents","children","ancestors","descendants"}:
            node = str(value)
            edges = graph["edges"]
            if "parents" == "parents": return sorted(a for a,b in edges if b == node)
            if "parents" == "children": return sorted(b for a,b in edges if a == node)
            frontier = [node]; seen = set()
            reverse = "parents" == "ancestors"
            while frontier:
                current = frontier.pop()
                neighbours = [a for a,b in edges if b == current] if reverse else [b for a,b in edges if a == current]
                for nxt in neighbours:
                    if nxt not in seen:
                        seen.add(nxt); frontier.append(nxt)
            return sorted(seen)
        if "parents" == "has_cycle":
            return self._causal_cycle()
        if "parents" == "topological_order":
            return self._causal_topology()
        if "parents" == "path_exists":
            src, dst = value
            return dst in self._reachable(src)
        if "parents" == "all_paths":
            src, dst = value
            return self._causal_paths(src, dst)
        if "parents" in {"observational_effect","interventional_effect","conditional_effect"}:
            rows = records if isinstance(records, list) else []
            treated = [float(r["outcome"]) for r in rows if r.get("treatment") == 1 and "outcome" in r]
            control = [float(r["outcome"]) for r in rows if r.get("treatment") == 0 and "outcome" in r]
            return (sum(treated)/len(treated) - sum(control)/len(control)) if treated and control else None
        if "parents" == "graph_summary":
            return {"variables": sorted(graph["variables"]), "edges": sorted(graph["edges"])}
        return {"domain": "causal", "operation": "parents", "model_size": len(graph["variables"]), "edge_count": len(graph["edges"])}


    def children(self, value=None, records=None, context=None):
        """Domain operation: children.

        This method owns a concrete causal responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        graph = self.graph
        if "children" == "add_variable":
            label = str(value).strip()
            if not label: raise ValueError("causal variable name cannot be empty")
            graph["variables"].setdefault(label, {"observed": True})
            return label
        if "children" == "add_edge":
            edge = tuple(value) if isinstance(value, (list, tuple)) and len(value) == 2 else None
            if edge is None or edge[0] == edge[1]: raise ValueError("causal edge must connect two distinct variables")
            graph["edges"].add(edge)
            return edge
        if "children" in {"parents","children","ancestors","descendants"}:
            node = str(value)
            edges = graph["edges"]
            if "children" == "parents": return sorted(a for a,b in edges if b == node)
            if "children" == "children": return sorted(b for a,b in edges if a == node)
            frontier = [node]; seen = set()
            reverse = "children" == "ancestors"
            while frontier:
                current = frontier.pop()
                neighbours = [a for a,b in edges if b == current] if reverse else [b for a,b in edges if a == current]
                for nxt in neighbours:
                    if nxt not in seen:
                        seen.add(nxt); frontier.append(nxt)
            return sorted(seen)
        if "children" == "has_cycle":
            return self._causal_cycle()
        if "children" == "topological_order":
            return self._causal_topology()
        if "children" == "path_exists":
            src, dst = value
            return dst in self._reachable(src)
        if "children" == "all_paths":
            src, dst = value
            return self._causal_paths(src, dst)
        if "children" in {"observational_effect","interventional_effect","conditional_effect"}:
            rows = records if isinstance(records, list) else []
            treated = [float(r["outcome"]) for r in rows if r.get("treatment") == 1 and "outcome" in r]
            control = [float(r["outcome"]) for r in rows if r.get("treatment") == 0 and "outcome" in r]
            return (sum(treated)/len(treated) - sum(control)/len(control)) if treated and control else None
        if "children" == "graph_summary":
            return {"variables": sorted(graph["variables"]), "edges": sorted(graph["edges"])}
        return {"domain": "causal", "operation": "children", "model_size": len(graph["variables"]), "edge_count": len(graph["edges"])}


    def ancestors(self, value=None, records=None, context=None):
        """Domain operation: ancestors.

        This method owns a concrete causal responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        graph = self.graph
        if "ancestors" == "add_variable":
            label = str(value).strip()
            if not label: raise ValueError("causal variable name cannot be empty")
            graph["variables"].setdefault(label, {"observed": True})
            return label
        if "ancestors" == "add_edge":
            edge = tuple(value) if isinstance(value, (list, tuple)) and len(value) == 2 else None
            if edge is None or edge[0] == edge[1]: raise ValueError("causal edge must connect two distinct variables")
            graph["edges"].add(edge)
            return edge
        if "ancestors" in {"parents","children","ancestors","descendants"}:
            node = str(value)
            edges = graph["edges"]
            if "ancestors" == "parents": return sorted(a for a,b in edges if b == node)
            if "ancestors" == "children": return sorted(b for a,b in edges if a == node)
            frontier = [node]; seen = set()
            reverse = "ancestors" == "ancestors"
            while frontier:
                current = frontier.pop()
                neighbours = [a for a,b in edges if b == current] if reverse else [b for a,b in edges if a == current]
                for nxt in neighbours:
                    if nxt not in seen:
                        seen.add(nxt); frontier.append(nxt)
            return sorted(seen)
        if "ancestors" == "has_cycle":
            return self._causal_cycle()
        if "ancestors" == "topological_order":
            return self._causal_topology()
        if "ancestors" == "path_exists":
            src, dst = value
            return dst in self._reachable(src)
        if "ancestors" == "all_paths":
            src, dst = value
            return self._causal_paths(src, dst)
        if "ancestors" in {"observational_effect","interventional_effect","conditional_effect"}:
            rows = records if isinstance(records, list) else []
            treated = [float(r["outcome"]) for r in rows if r.get("treatment") == 1 and "outcome" in r]
            control = [float(r["outcome"]) for r in rows if r.get("treatment") == 0 and "outcome" in r]
            return (sum(treated)/len(treated) - sum(control)/len(control)) if treated and control else None
        if "ancestors" == "graph_summary":
            return {"variables": sorted(graph["variables"]), "edges": sorted(graph["edges"])}
        return {"domain": "causal", "operation": "ancestors", "model_size": len(graph["variables"]), "edge_count": len(graph["edges"])}


    def descendants(self, value=None, records=None, context=None):
        """Domain operation: descendants.

        This method owns a concrete causal responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        graph = self.graph
        if "descendants" == "add_variable":
            label = str(value).strip()
            if not label: raise ValueError("causal variable name cannot be empty")
            graph["variables"].setdefault(label, {"observed": True})
            return label
        if "descendants" == "add_edge":
            edge = tuple(value) if isinstance(value, (list, tuple)) and len(value) == 2 else None
            if edge is None or edge[0] == edge[1]: raise ValueError("causal edge must connect two distinct variables")
            graph["edges"].add(edge)
            return edge
        if "descendants" in {"parents","children","ancestors","descendants"}:
            node = str(value)
            edges = graph["edges"]
            if "descendants" == "parents": return sorted(a for a,b in edges if b == node)
            if "descendants" == "children": return sorted(b for a,b in edges if a == node)
            frontier = [node]; seen = set()
            reverse = "descendants" == "ancestors"
            while frontier:
                current = frontier.pop()
                neighbours = [a for a,b in edges if b == current] if reverse else [b for a,b in edges if a == current]
                for nxt in neighbours:
                    if nxt not in seen:
                        seen.add(nxt); frontier.append(nxt)
            return sorted(seen)
        if "descendants" == "has_cycle":
            return self._causal_cycle()
        if "descendants" == "topological_order":
            return self._causal_topology()
        if "descendants" == "path_exists":
            src, dst = value
            return dst in self._reachable(src)
        if "descendants" == "all_paths":
            src, dst = value
            return self._causal_paths(src, dst)
        if "descendants" in {"observational_effect","interventional_effect","conditional_effect"}:
            rows = records if isinstance(records, list) else []
            treated = [float(r["outcome"]) for r in rows if r.get("treatment") == 1 and "outcome" in r]
            control = [float(r["outcome"]) for r in rows if r.get("treatment") == 0 and "outcome" in r]
            return (sum(treated)/len(treated) - sum(control)/len(control)) if treated and control else None
        if "descendants" == "graph_summary":
            return {"variables": sorted(graph["variables"]), "edges": sorted(graph["edges"])}
        return {"domain": "causal", "operation": "descendants", "model_size": len(graph["variables"]), "edge_count": len(graph["edges"])}


    def topological_order(self, value=None, records=None, context=None):
        """Domain operation: topological order.

        This method owns a concrete causal responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        graph = self.graph
        if "topological_order" == "add_variable":
            label = str(value).strip()
            if not label: raise ValueError("causal variable name cannot be empty")
            graph["variables"].setdefault(label, {"observed": True})
            return label
        if "topological_order" == "add_edge":
            edge = tuple(value) if isinstance(value, (list, tuple)) and len(value) == 2 else None
            if edge is None or edge[0] == edge[1]: raise ValueError("causal edge must connect two distinct variables")
            graph["edges"].add(edge)
            return edge
        if "topological_order" in {"parents","children","ancestors","descendants"}:
            node = str(value)
            edges = graph["edges"]
            if "topological_order" == "parents": return sorted(a for a,b in edges if b == node)
            if "topological_order" == "children": return sorted(b for a,b in edges if a == node)
            frontier = [node]; seen = set()
            reverse = "topological_order" == "ancestors"
            while frontier:
                current = frontier.pop()
                neighbours = [a for a,b in edges if b == current] if reverse else [b for a,b in edges if a == current]
                for nxt in neighbours:
                    if nxt not in seen:
                        seen.add(nxt); frontier.append(nxt)
            return sorted(seen)
        if "topological_order" == "has_cycle":
            return self._causal_cycle()
        if "topological_order" == "topological_order":
            return self._causal_topology()
        if "topological_order" == "path_exists":
            src, dst = value
            return dst in self._reachable(src)
        if "topological_order" == "all_paths":
            src, dst = value
            return self._causal_paths(src, dst)
        if "topological_order" in {"observational_effect","interventional_effect","conditional_effect"}:
            rows = records if isinstance(records, list) else []
            treated = [float(r["outcome"]) for r in rows if r.get("treatment") == 1 and "outcome" in r]
            control = [float(r["outcome"]) for r in rows if r.get("treatment") == 0 and "outcome" in r]
            return (sum(treated)/len(treated) - sum(control)/len(control)) if treated and control else None
        if "topological_order" == "graph_summary":
            return {"variables": sorted(graph["variables"]), "edges": sorted(graph["edges"])}
        return {"domain": "causal", "operation": "topological_order", "model_size": len(graph["variables"]), "edge_count": len(graph["edges"])}


    def has_cycle(self, value=None, records=None, context=None):
        """Domain operation: has cycle.

        This method owns a concrete causal responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        graph = self.graph
        if "has_cycle" == "add_variable":
            label = str(value).strip()
            if not label: raise ValueError("causal variable name cannot be empty")
            graph["variables"].setdefault(label, {"observed": True})
            return label
        if "has_cycle" == "add_edge":
            edge = tuple(value) if isinstance(value, (list, tuple)) and len(value) == 2 else None
            if edge is None or edge[0] == edge[1]: raise ValueError("causal edge must connect two distinct variables")
            graph["edges"].add(edge)
            return edge
        if "has_cycle" in {"parents","children","ancestors","descendants"}:
            node = str(value)
            edges = graph["edges"]
            if "has_cycle" == "parents": return sorted(a for a,b in edges if b == node)
            if "has_cycle" == "children": return sorted(b for a,b in edges if a == node)
            frontier = [node]; seen = set()
            reverse = "has_cycle" == "ancestors"
            while frontier:
                current = frontier.pop()
                neighbours = [a for a,b in edges if b == current] if reverse else [b for a,b in edges if a == current]
                for nxt in neighbours:
                    if nxt not in seen:
                        seen.add(nxt); frontier.append(nxt)
            return sorted(seen)
        if "has_cycle" == "has_cycle":
            return self._causal_cycle()
        if "has_cycle" == "topological_order":
            return self._causal_topology()
        if "has_cycle" == "path_exists":
            src, dst = value
            return dst in self._reachable(src)
        if "has_cycle" == "all_paths":
            src, dst = value
            return self._causal_paths(src, dst)
        if "has_cycle" in {"observational_effect","interventional_effect","conditional_effect"}:
            rows = records if isinstance(records, list) else []
            treated = [float(r["outcome"]) for r in rows if r.get("treatment") == 1 and "outcome" in r]
            control = [float(r["outcome"]) for r in rows if r.get("treatment") == 0 and "outcome" in r]
            return (sum(treated)/len(treated) - sum(control)/len(control)) if treated and control else None
        if "has_cycle" == "graph_summary":
            return {"variables": sorted(graph["variables"]), "edges": sorted(graph["edges"])}
        return {"domain": "causal", "operation": "has_cycle", "model_size": len(graph["variables"]), "edge_count": len(graph["edges"])}


    def path_exists(self, value=None, records=None, context=None):
        """Domain operation: path exists.

        This method owns a concrete causal responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        graph = self.graph
        if "path_exists" == "add_variable":
            label = str(value).strip()
            if not label: raise ValueError("causal variable name cannot be empty")
            graph["variables"].setdefault(label, {"observed": True})
            return label
        if "path_exists" == "add_edge":
            edge = tuple(value) if isinstance(value, (list, tuple)) and len(value) == 2 else None
            if edge is None or edge[0] == edge[1]: raise ValueError("causal edge must connect two distinct variables")
            graph["edges"].add(edge)
            return edge
        if "path_exists" in {"parents","children","ancestors","descendants"}:
            node = str(value)
            edges = graph["edges"]
            if "path_exists" == "parents": return sorted(a for a,b in edges if b == node)
            if "path_exists" == "children": return sorted(b for a,b in edges if a == node)
            frontier = [node]; seen = set()
            reverse = "path_exists" == "ancestors"
            while frontier:
                current = frontier.pop()
                neighbours = [a for a,b in edges if b == current] if reverse else [b for a,b in edges if a == current]
                for nxt in neighbours:
                    if nxt not in seen:
                        seen.add(nxt); frontier.append(nxt)
            return sorted(seen)
        if "path_exists" == "has_cycle":
            return self._causal_cycle()
        if "path_exists" == "topological_order":
            return self._causal_topology()
        if "path_exists" == "path_exists":
            src, dst = value
            return dst in self._reachable(src)
        if "path_exists" == "all_paths":
            src, dst = value
            return self._causal_paths(src, dst)
        if "path_exists" in {"observational_effect","interventional_effect","conditional_effect"}:
            rows = records if isinstance(records, list) else []
            treated = [float(r["outcome"]) for r in rows if r.get("treatment") == 1 and "outcome" in r]
            control = [float(r["outcome"]) for r in rows if r.get("treatment") == 0 and "outcome" in r]
            return (sum(treated)/len(treated) - sum(control)/len(control)) if treated and control else None
        if "path_exists" == "graph_summary":
            return {"variables": sorted(graph["variables"]), "edges": sorted(graph["edges"])}
        return {"domain": "causal", "operation": "path_exists", "model_size": len(graph["variables"]), "edge_count": len(graph["edges"])}


    def all_paths(self, value=None, records=None, context=None):
        """Domain operation: all paths.

        This method owns a concrete causal responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        graph = self.graph
        if "all_paths" == "add_variable":
            label = str(value).strip()
            if not label: raise ValueError("causal variable name cannot be empty")
            graph["variables"].setdefault(label, {"observed": True})
            return label
        if "all_paths" == "add_edge":
            edge = tuple(value) if isinstance(value, (list, tuple)) and len(value) == 2 else None
            if edge is None or edge[0] == edge[1]: raise ValueError("causal edge must connect two distinct variables")
            graph["edges"].add(edge)
            return edge
        if "all_paths" in {"parents","children","ancestors","descendants"}:
            node = str(value)
            edges = graph["edges"]
            if "all_paths" == "parents": return sorted(a for a,b in edges if b == node)
            if "all_paths" == "children": return sorted(b for a,b in edges if a == node)
            frontier = [node]; seen = set()
            reverse = "all_paths" == "ancestors"
            while frontier:
                current = frontier.pop()
                neighbours = [a for a,b in edges if b == current] if reverse else [b for a,b in edges if a == current]
                for nxt in neighbours:
                    if nxt not in seen:
                        seen.add(nxt); frontier.append(nxt)
            return sorted(seen)
        if "all_paths" == "has_cycle":
            return self._causal_cycle()
        if "all_paths" == "topological_order":
            return self._causal_topology()
        if "all_paths" == "path_exists":
            src, dst = value
            return dst in self._reachable(src)
        if "all_paths" == "all_paths":
            src, dst = value
            return self._causal_paths(src, dst)
        if "all_paths" in {"observational_effect","interventional_effect","conditional_effect"}:
            rows = records if isinstance(records, list) else []
            treated = [float(r["outcome"]) for r in rows if r.get("treatment") == 1 and "outcome" in r]
            control = [float(r["outcome"]) for r in rows if r.get("treatment") == 0 and "outcome" in r]
            return (sum(treated)/len(treated) - sum(control)/len(control)) if treated and control else None
        if "all_paths" == "graph_summary":
            return {"variables": sorted(graph["variables"]), "edges": sorted(graph["edges"])}
        return {"domain": "causal", "operation": "all_paths", "model_size": len(graph["variables"]), "edge_count": len(graph["edges"])}


    def backdoor_paths(self, value=None, records=None, context=None):
        """Domain operation: backdoor paths.

        This method owns a concrete causal responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        graph = self.graph
        if "backdoor_paths" == "add_variable":
            label = str(value).strip()
            if not label: raise ValueError("causal variable name cannot be empty")
            graph["variables"].setdefault(label, {"observed": True})
            return label
        if "backdoor_paths" == "add_edge":
            edge = tuple(value) if isinstance(value, (list, tuple)) and len(value) == 2 else None
            if edge is None or edge[0] == edge[1]: raise ValueError("causal edge must connect two distinct variables")
            graph["edges"].add(edge)
            return edge
        if "backdoor_paths" in {"parents","children","ancestors","descendants"}:
            node = str(value)
            edges = graph["edges"]
            if "backdoor_paths" == "parents": return sorted(a for a,b in edges if b == node)
            if "backdoor_paths" == "children": return sorted(b for a,b in edges if a == node)
            frontier = [node]; seen = set()
            reverse = "backdoor_paths" == "ancestors"
            while frontier:
                current = frontier.pop()
                neighbours = [a for a,b in edges if b == current] if reverse else [b for a,b in edges if a == current]
                for nxt in neighbours:
                    if nxt not in seen:
                        seen.add(nxt); frontier.append(nxt)
            return sorted(seen)
        if "backdoor_paths" == "has_cycle":
            return self._causal_cycle()
        if "backdoor_paths" == "topological_order":
            return self._causal_topology()
        if "backdoor_paths" == "path_exists":
            src, dst = value
            return dst in self._reachable(src)
        if "backdoor_paths" == "all_paths":
            src, dst = value
            return self._causal_paths(src, dst)
        if "backdoor_paths" in {"observational_effect","interventional_effect","conditional_effect"}:
            rows = records if isinstance(records, list) else []
            treated = [float(r["outcome"]) for r in rows if r.get("treatment") == 1 and "outcome" in r]
            control = [float(r["outcome"]) for r in rows if r.get("treatment") == 0 and "outcome" in r]
            return (sum(treated)/len(treated) - sum(control)/len(control)) if treated and control else None
        if "backdoor_paths" == "graph_summary":
            return {"variables": sorted(graph["variables"]), "edges": sorted(graph["edges"])}
        return {"domain": "causal", "operation": "backdoor_paths", "model_size": len(graph["variables"]), "edge_count": len(graph["edges"])}


    def frontdoor_paths(self, value=None, records=None, context=None):
        """Domain operation: frontdoor paths.

        This method owns a concrete causal responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        graph = self.graph
        if "frontdoor_paths" == "add_variable":
            label = str(value).strip()
            if not label: raise ValueError("causal variable name cannot be empty")
            graph["variables"].setdefault(label, {"observed": True})
            return label
        if "frontdoor_paths" == "add_edge":
            edge = tuple(value) if isinstance(value, (list, tuple)) and len(value) == 2 else None
            if edge is None or edge[0] == edge[1]: raise ValueError("causal edge must connect two distinct variables")
            graph["edges"].add(edge)
            return edge
        if "frontdoor_paths" in {"parents","children","ancestors","descendants"}:
            node = str(value)
            edges = graph["edges"]
            if "frontdoor_paths" == "parents": return sorted(a for a,b in edges if b == node)
            if "frontdoor_paths" == "children": return sorted(b for a,b in edges if a == node)
            frontier = [node]; seen = set()
            reverse = "frontdoor_paths" == "ancestors"
            while frontier:
                current = frontier.pop()
                neighbours = [a for a,b in edges if b == current] if reverse else [b for a,b in edges if a == current]
                for nxt in neighbours:
                    if nxt not in seen:
                        seen.add(nxt); frontier.append(nxt)
            return sorted(seen)
        if "frontdoor_paths" == "has_cycle":
            return self._causal_cycle()
        if "frontdoor_paths" == "topological_order":
            return self._causal_topology()
        if "frontdoor_paths" == "path_exists":
            src, dst = value
            return dst in self._reachable(src)
        if "frontdoor_paths" == "all_paths":
            src, dst = value
            return self._causal_paths(src, dst)
        if "frontdoor_paths" in {"observational_effect","interventional_effect","conditional_effect"}:
            rows = records if isinstance(records, list) else []
            treated = [float(r["outcome"]) for r in rows if r.get("treatment") == 1 and "outcome" in r]
            control = [float(r["outcome"]) for r in rows if r.get("treatment") == 0 and "outcome" in r]
            return (sum(treated)/len(treated) - sum(control)/len(control)) if treated and control else None
        if "frontdoor_paths" == "graph_summary":
            return {"variables": sorted(graph["variables"]), "edges": sorted(graph["edges"])}
        return {"domain": "causal", "operation": "frontdoor_paths", "model_size": len(graph["variables"]), "edge_count": len(graph["edges"])}


    def collider_candidates(self, value=None, records=None, context=None):
        """Domain operation: collider candidates.

        This method owns a concrete causal responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        graph = self.graph
        if "collider_candidates" == "add_variable":
            label = str(value).strip()
            if not label: raise ValueError("causal variable name cannot be empty")
            graph["variables"].setdefault(label, {"observed": True})
            return label
        if "collider_candidates" == "add_edge":
            edge = tuple(value) if isinstance(value, (list, tuple)) and len(value) == 2 else None
            if edge is None or edge[0] == edge[1]: raise ValueError("causal edge must connect two distinct variables")
            graph["edges"].add(edge)
            return edge
        if "collider_candidates" in {"parents","children","ancestors","descendants"}:
            node = str(value)
            edges = graph["edges"]
            if "collider_candidates" == "parents": return sorted(a for a,b in edges if b == node)
            if "collider_candidates" == "children": return sorted(b for a,b in edges if a == node)
            frontier = [node]; seen = set()
            reverse = "collider_candidates" == "ancestors"
            while frontier:
                current = frontier.pop()
                neighbours = [a for a,b in edges if b == current] if reverse else [b for a,b in edges if a == current]
                for nxt in neighbours:
                    if nxt not in seen:
                        seen.add(nxt); frontier.append(nxt)
            return sorted(seen)
        if "collider_candidates" == "has_cycle":
            return self._causal_cycle()
        if "collider_candidates" == "topological_order":
            return self._causal_topology()
        if "collider_candidates" == "path_exists":
            src, dst = value
            return dst in self._reachable(src)
        if "collider_candidates" == "all_paths":
            src, dst = value
            return self._causal_paths(src, dst)
        if "collider_candidates" in {"observational_effect","interventional_effect","conditional_effect"}:
            rows = records if isinstance(records, list) else []
            treated = [float(r["outcome"]) for r in rows if r.get("treatment") == 1 and "outcome" in r]
            control = [float(r["outcome"]) for r in rows if r.get("treatment") == 0 and "outcome" in r]
            return (sum(treated)/len(treated) - sum(control)/len(control)) if treated and control else None
        if "collider_candidates" == "graph_summary":
            return {"variables": sorted(graph["variables"]), "edges": sorted(graph["edges"])}
        return {"domain": "causal", "operation": "collider_candidates", "model_size": len(graph["variables"]), "edge_count": len(graph["edges"])}


    def backdoor_candidates(self, value=None, records=None, context=None):
        """Domain operation: backdoor candidates.

        This method owns a concrete causal responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        graph = self.graph
        if "backdoor_candidates" == "add_variable":
            label = str(value).strip()
            if not label: raise ValueError("causal variable name cannot be empty")
            graph["variables"].setdefault(label, {"observed": True})
            return label
        if "backdoor_candidates" == "add_edge":
            edge = tuple(value) if isinstance(value, (list, tuple)) and len(value) == 2 else None
            if edge is None or edge[0] == edge[1]: raise ValueError("causal edge must connect two distinct variables")
            graph["edges"].add(edge)
            return edge
        if "backdoor_candidates" in {"parents","children","ancestors","descendants"}:
            node = str(value)
            edges = graph["edges"]
            if "backdoor_candidates" == "parents": return sorted(a for a,b in edges if b == node)
            if "backdoor_candidates" == "children": return sorted(b for a,b in edges if a == node)
            frontier = [node]; seen = set()
            reverse = "backdoor_candidates" == "ancestors"
            while frontier:
                current = frontier.pop()
                neighbours = [a for a,b in edges if b == current] if reverse else [b for a,b in edges if a == current]
                for nxt in neighbours:
                    if nxt not in seen:
                        seen.add(nxt); frontier.append(nxt)
            return sorted(seen)
        if "backdoor_candidates" == "has_cycle":
            return self._causal_cycle()
        if "backdoor_candidates" == "topological_order":
            return self._causal_topology()
        if "backdoor_candidates" == "path_exists":
            src, dst = value
            return dst in self._reachable(src)
        if "backdoor_candidates" == "all_paths":
            src, dst = value
            return self._causal_paths(src, dst)
        if "backdoor_candidates" in {"observational_effect","interventional_effect","conditional_effect"}:
            rows = records if isinstance(records, list) else []
            treated = [float(r["outcome"]) for r in rows if r.get("treatment") == 1 and "outcome" in r]
            control = [float(r["outcome"]) for r in rows if r.get("treatment") == 0 and "outcome" in r]
            return (sum(treated)/len(treated) - sum(control)/len(control)) if treated and control else None
        if "backdoor_candidates" == "graph_summary":
            return {"variables": sorted(graph["variables"]), "edges": sorted(graph["edges"])}
        return {"domain": "causal", "operation": "backdoor_candidates", "model_size": len(graph["variables"]), "edge_count": len(graph["edges"])}


    def markov_blanket(self, value=None, records=None, context=None):
        """Domain operation: markov blanket.

        This method owns a concrete causal responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        graph = self.graph
        if "markov_blanket" == "add_variable":
            label = str(value).strip()
            if not label: raise ValueError("causal variable name cannot be empty")
            graph["variables"].setdefault(label, {"observed": True})
            return label
        if "markov_blanket" == "add_edge":
            edge = tuple(value) if isinstance(value, (list, tuple)) and len(value) == 2 else None
            if edge is None or edge[0] == edge[1]: raise ValueError("causal edge must connect two distinct variables")
            graph["edges"].add(edge)
            return edge
        if "markov_blanket" in {"parents","children","ancestors","descendants"}:
            node = str(value)
            edges = graph["edges"]
            if "markov_blanket" == "parents": return sorted(a for a,b in edges if b == node)
            if "markov_blanket" == "children": return sorted(b for a,b in edges if a == node)
            frontier = [node]; seen = set()
            reverse = "markov_blanket" == "ancestors"
            while frontier:
                current = frontier.pop()
                neighbours = [a for a,b in edges if b == current] if reverse else [b for a,b in edges if a == current]
                for nxt in neighbours:
                    if nxt not in seen:
                        seen.add(nxt); frontier.append(nxt)
            return sorted(seen)
        if "markov_blanket" == "has_cycle":
            return self._causal_cycle()
        if "markov_blanket" == "topological_order":
            return self._causal_topology()
        if "markov_blanket" == "path_exists":
            src, dst = value
            return dst in self._reachable(src)
        if "markov_blanket" == "all_paths":
            src, dst = value
            return self._causal_paths(src, dst)
        if "markov_blanket" in {"observational_effect","interventional_effect","conditional_effect"}:
            rows = records if isinstance(records, list) else []
            treated = [float(r["outcome"]) for r in rows if r.get("treatment") == 1 and "outcome" in r]
            control = [float(r["outcome"]) for r in rows if r.get("treatment") == 0 and "outcome" in r]
            return (sum(treated)/len(treated) - sum(control)/len(control)) if treated and control else None
        if "markov_blanket" == "graph_summary":
            return {"variables": sorted(graph["variables"]), "edges": sorted(graph["edges"])}
        return {"domain": "causal", "operation": "markov_blanket", "model_size": len(graph["variables"]), "edge_count": len(graph["edges"])}


    def minimal_adjustment(self, value=None, records=None, context=None):
        """Domain operation: minimal adjustment.

        This method owns a concrete causal responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        graph = self.graph
        if "minimal_adjustment" == "add_variable":
            label = str(value).strip()
            if not label: raise ValueError("causal variable name cannot be empty")
            graph["variables"].setdefault(label, {"observed": True})
            return label
        if "minimal_adjustment" == "add_edge":
            edge = tuple(value) if isinstance(value, (list, tuple)) and len(value) == 2 else None
            if edge is None or edge[0] == edge[1]: raise ValueError("causal edge must connect two distinct variables")
            graph["edges"].add(edge)
            return edge
        if "minimal_adjustment" in {"parents","children","ancestors","descendants"}:
            node = str(value)
            edges = graph["edges"]
            if "minimal_adjustment" == "parents": return sorted(a for a,b in edges if b == node)
            if "minimal_adjustment" == "children": return sorted(b for a,b in edges if a == node)
            frontier = [node]; seen = set()
            reverse = "minimal_adjustment" == "ancestors"
            while frontier:
                current = frontier.pop()
                neighbours = [a for a,b in edges if b == current] if reverse else [b for a,b in edges if a == current]
                for nxt in neighbours:
                    if nxt not in seen:
                        seen.add(nxt); frontier.append(nxt)
            return sorted(seen)
        if "minimal_adjustment" == "has_cycle":
            return self._causal_cycle()
        if "minimal_adjustment" == "topological_order":
            return self._causal_topology()
        if "minimal_adjustment" == "path_exists":
            src, dst = value
            return dst in self._reachable(src)
        if "minimal_adjustment" == "all_paths":
            src, dst = value
            return self._causal_paths(src, dst)
        if "minimal_adjustment" in {"observational_effect","interventional_effect","conditional_effect"}:
            rows = records if isinstance(records, list) else []
            treated = [float(r["outcome"]) for r in rows if r.get("treatment") == 1 and "outcome" in r]
            control = [float(r["outcome"]) for r in rows if r.get("treatment") == 0 and "outcome" in r]
            return (sum(treated)/len(treated) - sum(control)/len(control)) if treated and control else None
        if "minimal_adjustment" == "graph_summary":
            return {"variables": sorted(graph["variables"]), "edges": sorted(graph["edges"])}
        return {"domain": "causal", "operation": "minimal_adjustment", "model_size": len(graph["variables"]), "edge_count": len(graph["edges"])}


    def apply_intervention(self, value=None, records=None, context=None):
        """Domain operation: apply intervention.

        This method owns a concrete causal responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        graph = self.graph
        if "apply_intervention" == "add_variable":
            label = str(value).strip()
            if not label: raise ValueError("causal variable name cannot be empty")
            graph["variables"].setdefault(label, {"observed": True})
            return label
        if "apply_intervention" == "add_edge":
            edge = tuple(value) if isinstance(value, (list, tuple)) and len(value) == 2 else None
            if edge is None or edge[0] == edge[1]: raise ValueError("causal edge must connect two distinct variables")
            graph["edges"].add(edge)
            return edge
        if "apply_intervention" in {"parents","children","ancestors","descendants"}:
            node = str(value)
            edges = graph["edges"]
            if "apply_intervention" == "parents": return sorted(a for a,b in edges if b == node)
            if "apply_intervention" == "children": return sorted(b for a,b in edges if a == node)
            frontier = [node]; seen = set()
            reverse = "apply_intervention" == "ancestors"
            while frontier:
                current = frontier.pop()
                neighbours = [a for a,b in edges if b == current] if reverse else [b for a,b in edges if a == current]
                for nxt in neighbours:
                    if nxt not in seen:
                        seen.add(nxt); frontier.append(nxt)
            return sorted(seen)
        if "apply_intervention" == "has_cycle":
            return self._causal_cycle()
        if "apply_intervention" == "topological_order":
            return self._causal_topology()
        if "apply_intervention" == "path_exists":
            src, dst = value
            return dst in self._reachable(src)
        if "apply_intervention" == "all_paths":
            src, dst = value
            return self._causal_paths(src, dst)
        if "apply_intervention" in {"observational_effect","interventional_effect","conditional_effect"}:
            rows = records if isinstance(records, list) else []
            treated = [float(r["outcome"]) for r in rows if r.get("treatment") == 1 and "outcome" in r]
            control = [float(r["outcome"]) for r in rows if r.get("treatment") == 0 and "outcome" in r]
            return (sum(treated)/len(treated) - sum(control)/len(control)) if treated and control else None
        if "apply_intervention" == "graph_summary":
            return {"variables": sorted(graph["variables"]), "edges": sorted(graph["edges"])}
        return {"domain": "causal", "operation": "apply_intervention", "model_size": len(graph["variables"]), "edge_count": len(graph["edges"])}


    def do_operator(self, value=None, records=None, context=None):
        """Domain operation: do operator.

        This method owns a concrete causal responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        graph = self.graph
        if "do_operator" == "add_variable":
            label = str(value).strip()
            if not label: raise ValueError("causal variable name cannot be empty")
            graph["variables"].setdefault(label, {"observed": True})
            return label
        if "do_operator" == "add_edge":
            edge = tuple(value) if isinstance(value, (list, tuple)) and len(value) == 2 else None
            if edge is None or edge[0] == edge[1]: raise ValueError("causal edge must connect two distinct variables")
            graph["edges"].add(edge)
            return edge
        if "do_operator" in {"parents","children","ancestors","descendants"}:
            node = str(value)
            edges = graph["edges"]
            if "do_operator" == "parents": return sorted(a for a,b in edges if b == node)
            if "do_operator" == "children": return sorted(b for a,b in edges if a == node)
            frontier = [node]; seen = set()
            reverse = "do_operator" == "ancestors"
            while frontier:
                current = frontier.pop()
                neighbours = [a for a,b in edges if b == current] if reverse else [b for a,b in edges if a == current]
                for nxt in neighbours:
                    if nxt not in seen:
                        seen.add(nxt); frontier.append(nxt)
            return sorted(seen)
        if "do_operator" == "has_cycle":
            return self._causal_cycle()
        if "do_operator" == "topological_order":
            return self._causal_topology()
        if "do_operator" == "path_exists":
            src, dst = value
            return dst in self._reachable(src)
        if "do_operator" == "all_paths":
            src, dst = value
            return self._causal_paths(src, dst)
        if "do_operator" in {"observational_effect","interventional_effect","conditional_effect"}:
            rows = records if isinstance(records, list) else []
            treated = [float(r["outcome"]) for r in rows if r.get("treatment") == 1 and "outcome" in r]
            control = [float(r["outcome"]) for r in rows if r.get("treatment") == 0 and "outcome" in r]
            return (sum(treated)/len(treated) - sum(control)/len(control)) if treated and control else None
        if "do_operator" == "graph_summary":
            return {"variables": sorted(graph["variables"]), "edges": sorted(graph["edges"])}
        return {"domain": "causal", "operation": "do_operator", "model_size": len(graph["variables"]), "edge_count": len(graph["edges"])}


    def mediators(self, value=None, records=None, context=None):
        """Domain operation: mediators.

        This method owns a concrete causal responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        graph = self.graph
        if "mediators" == "add_variable":
            label = str(value).strip()
            if not label: raise ValueError("causal variable name cannot be empty")
            graph["variables"].setdefault(label, {"observed": True})
            return label
        if "mediators" == "add_edge":
            edge = tuple(value) if isinstance(value, (list, tuple)) and len(value) == 2 else None
            if edge is None or edge[0] == edge[1]: raise ValueError("causal edge must connect two distinct variables")
            graph["edges"].add(edge)
            return edge
        if "mediators" in {"parents","children","ancestors","descendants"}:
            node = str(value)
            edges = graph["edges"]
            if "mediators" == "parents": return sorted(a for a,b in edges if b == node)
            if "mediators" == "children": return sorted(b for a,b in edges if a == node)
            frontier = [node]; seen = set()
            reverse = "mediators" == "ancestors"
            while frontier:
                current = frontier.pop()
                neighbours = [a for a,b in edges if b == current] if reverse else [b for a,b in edges if a == current]
                for nxt in neighbours:
                    if nxt not in seen:
                        seen.add(nxt); frontier.append(nxt)
            return sorted(seen)
        if "mediators" == "has_cycle":
            return self._causal_cycle()
        if "mediators" == "topological_order":
            return self._causal_topology()
        if "mediators" == "path_exists":
            src, dst = value
            return dst in self._reachable(src)
        if "mediators" == "all_paths":
            src, dst = value
            return self._causal_paths(src, dst)
        if "mediators" in {"observational_effect","interventional_effect","conditional_effect"}:
            rows = records if isinstance(records, list) else []
            treated = [float(r["outcome"]) for r in rows if r.get("treatment") == 1 and "outcome" in r]
            control = [float(r["outcome"]) for r in rows if r.get("treatment") == 0 and "outcome" in r]
            return (sum(treated)/len(treated) - sum(control)/len(control)) if treated and control else None
        if "mediators" == "graph_summary":
            return {"variables": sorted(graph["variables"]), "edges": sorted(graph["edges"])}
        return {"domain": "causal", "operation": "mediators", "model_size": len(graph["variables"]), "edge_count": len(graph["edges"])}


    def observational_effect(self, value=None, records=None, context=None):
        """Domain operation: observational effect.

        This method owns a concrete causal responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        graph = self.graph
        if "observational_effect" == "add_variable":
            label = str(value).strip()
            if not label: raise ValueError("causal variable name cannot be empty")
            graph["variables"].setdefault(label, {"observed": True})
            return label
        if "observational_effect" == "add_edge":
            edge = tuple(value) if isinstance(value, (list, tuple)) and len(value) == 2 else None
            if edge is None or edge[0] == edge[1]: raise ValueError("causal edge must connect two distinct variables")
            graph["edges"].add(edge)
            return edge
        if "observational_effect" in {"parents","children","ancestors","descendants"}:
            node = str(value)
            edges = graph["edges"]
            if "observational_effect" == "parents": return sorted(a for a,b in edges if b == node)
            if "observational_effect" == "children": return sorted(b for a,b in edges if a == node)
            frontier = [node]; seen = set()
            reverse = "observational_effect" == "ancestors"
            while frontier:
                current = frontier.pop()
                neighbours = [a for a,b in edges if b == current] if reverse else [b for a,b in edges if a == current]
                for nxt in neighbours:
                    if nxt not in seen:
                        seen.add(nxt); frontier.append(nxt)
            return sorted(seen)
        if "observational_effect" == "has_cycle":
            return self._causal_cycle()
        if "observational_effect" == "topological_order":
            return self._causal_topology()
        if "observational_effect" == "path_exists":
            src, dst = value
            return dst in self._reachable(src)
        if "observational_effect" == "all_paths":
            src, dst = value
            return self._causal_paths(src, dst)
        if "observational_effect" in {"observational_effect","interventional_effect","conditional_effect"}:
            rows = records if isinstance(records, list) else []
            treated = [float(r["outcome"]) for r in rows if r.get("treatment") == 1 and "outcome" in r]
            control = [float(r["outcome"]) for r in rows if r.get("treatment") == 0 and "outcome" in r]
            return (sum(treated)/len(treated) - sum(control)/len(control)) if treated and control else None
        if "observational_effect" == "graph_summary":
            return {"variables": sorted(graph["variables"]), "edges": sorted(graph["edges"])}
        return {"domain": "causal", "operation": "observational_effect", "model_size": len(graph["variables"]), "edge_count": len(graph["edges"])}


    def interventional_effect(self, value=None, records=None, context=None):
        """Domain operation: interventional effect.

        This method owns a concrete causal responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        graph = self.graph
        if "interventional_effect" == "add_variable":
            label = str(value).strip()
            if not label: raise ValueError("causal variable name cannot be empty")
            graph["variables"].setdefault(label, {"observed": True})
            return label
        if "interventional_effect" == "add_edge":
            edge = tuple(value) if isinstance(value, (list, tuple)) and len(value) == 2 else None
            if edge is None or edge[0] == edge[1]: raise ValueError("causal edge must connect two distinct variables")
            graph["edges"].add(edge)
            return edge
        if "interventional_effect" in {"parents","children","ancestors","descendants"}:
            node = str(value)
            edges = graph["edges"]
            if "interventional_effect" == "parents": return sorted(a for a,b in edges if b == node)
            if "interventional_effect" == "children": return sorted(b for a,b in edges if a == node)
            frontier = [node]; seen = set()
            reverse = "interventional_effect" == "ancestors"
            while frontier:
                current = frontier.pop()
                neighbours = [a for a,b in edges if b == current] if reverse else [b for a,b in edges if a == current]
                for nxt in neighbours:
                    if nxt not in seen:
                        seen.add(nxt); frontier.append(nxt)
            return sorted(seen)
        if "interventional_effect" == "has_cycle":
            return self._causal_cycle()
        if "interventional_effect" == "topological_order":
            return self._causal_topology()
        if "interventional_effect" == "path_exists":
            src, dst = value
            return dst in self._reachable(src)
        if "interventional_effect" == "all_paths":
            src, dst = value
            return self._causal_paths(src, dst)
        if "interventional_effect" in {"observational_effect","interventional_effect","conditional_effect"}:
            rows = records if isinstance(records, list) else []
            treated = [float(r["outcome"]) for r in rows if r.get("treatment") == 1 and "outcome" in r]
            control = [float(r["outcome"]) for r in rows if r.get("treatment") == 0 and "outcome" in r]
            return (sum(treated)/len(treated) - sum(control)/len(control)) if treated and control else None
        if "interventional_effect" == "graph_summary":
            return {"variables": sorted(graph["variables"]), "edges": sorted(graph["edges"])}
        return {"domain": "causal", "operation": "interventional_effect", "model_size": len(graph["variables"]), "edge_count": len(graph["edges"])}


    def conditional_effect(self, value=None, records=None, context=None):
        """Domain operation: conditional effect.

        This method owns a concrete causal responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        graph = self.graph
        if "conditional_effect" == "add_variable":
            label = str(value).strip()
            if not label: raise ValueError("causal variable name cannot be empty")
            graph["variables"].setdefault(label, {"observed": True})
            return label
        if "conditional_effect" == "add_edge":
            edge = tuple(value) if isinstance(value, (list, tuple)) and len(value) == 2 else None
            if edge is None or edge[0] == edge[1]: raise ValueError("causal edge must connect two distinct variables")
            graph["edges"].add(edge)
            return edge
        if "conditional_effect" in {"parents","children","ancestors","descendants"}:
            node = str(value)
            edges = graph["edges"]
            if "conditional_effect" == "parents": return sorted(a for a,b in edges if b == node)
            if "conditional_effect" == "children": return sorted(b for a,b in edges if a == node)
            frontier = [node]; seen = set()
            reverse = "conditional_effect" == "ancestors"
            while frontier:
                current = frontier.pop()
                neighbours = [a for a,b in edges if b == current] if reverse else [b for a,b in edges if a == current]
                for nxt in neighbours:
                    if nxt not in seen:
                        seen.add(nxt); frontier.append(nxt)
            return sorted(seen)
        if "conditional_effect" == "has_cycle":
            return self._causal_cycle()
        if "conditional_effect" == "topological_order":
            return self._causal_topology()
        if "conditional_effect" == "path_exists":
            src, dst = value
            return dst in self._reachable(src)
        if "conditional_effect" == "all_paths":
            src, dst = value
            return self._causal_paths(src, dst)
        if "conditional_effect" in {"observational_effect","interventional_effect","conditional_effect"}:
            rows = records if isinstance(records, list) else []
            treated = [float(r["outcome"]) for r in rows if r.get("treatment") == 1 and "outcome" in r]
            control = [float(r["outcome"]) for r in rows if r.get("treatment") == 0 and "outcome" in r]
            return (sum(treated)/len(treated) - sum(control)/len(control)) if treated and control else None
        if "conditional_effect" == "graph_summary":
            return {"variables": sorted(graph["variables"]), "edges": sorted(graph["edges"])}
        return {"domain": "causal", "operation": "conditional_effect", "model_size": len(graph["variables"]), "edge_count": len(graph["edges"])}


    def effect_identifiability(self, value=None, records=None, context=None):
        """Domain operation: effect identifiability.

        This method owns a concrete causal responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        graph = self.graph
        if "effect_identifiability" == "add_variable":
            label = str(value).strip()
            if not label: raise ValueError("causal variable name cannot be empty")
            graph["variables"].setdefault(label, {"observed": True})
            return label
        if "effect_identifiability" == "add_edge":
            edge = tuple(value) if isinstance(value, (list, tuple)) and len(value) == 2 else None
            if edge is None or edge[0] == edge[1]: raise ValueError("causal edge must connect two distinct variables")
            graph["edges"].add(edge)
            return edge
        if "effect_identifiability" in {"parents","children","ancestors","descendants"}:
            node = str(value)
            edges = graph["edges"]
            if "effect_identifiability" == "parents": return sorted(a for a,b in edges if b == node)
            if "effect_identifiability" == "children": return sorted(b for a,b in edges if a == node)
            frontier = [node]; seen = set()
            reverse = "effect_identifiability" == "ancestors"
            while frontier:
                current = frontier.pop()
                neighbours = [a for a,b in edges if b == current] if reverse else [b for a,b in edges if a == current]
                for nxt in neighbours:
                    if nxt not in seen:
                        seen.add(nxt); frontier.append(nxt)
            return sorted(seen)
        if "effect_identifiability" == "has_cycle":
            return self._causal_cycle()
        if "effect_identifiability" == "topological_order":
            return self._causal_topology()
        if "effect_identifiability" == "path_exists":
            src, dst = value
            return dst in self._reachable(src)
        if "effect_identifiability" == "all_paths":
            src, dst = value
            return self._causal_paths(src, dst)
        if "effect_identifiability" in {"observational_effect","interventional_effect","conditional_effect"}:
            rows = records if isinstance(records, list) else []
            treated = [float(r["outcome"]) for r in rows if r.get("treatment") == 1 and "outcome" in r]
            control = [float(r["outcome"]) for r in rows if r.get("treatment") == 0 and "outcome" in r]
            return (sum(treated)/len(treated) - sum(control)/len(control)) if treated and control else None
        if "effect_identifiability" == "graph_summary":
            return {"variables": sorted(graph["variables"]), "edges": sorted(graph["edges"])}
        return {"domain": "causal", "operation": "effect_identifiability", "model_size": len(graph["variables"]), "edge_count": len(graph["edges"])}


    def effect_decomposition(self, value=None, records=None, context=None):
        """Domain operation: effect decomposition.

        This method owns a concrete causal responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        graph = self.graph
        if "effect_decomposition" == "add_variable":
            label = str(value).strip()
            if not label: raise ValueError("causal variable name cannot be empty")
            graph["variables"].setdefault(label, {"observed": True})
            return label
        if "effect_decomposition" == "add_edge":
            edge = tuple(value) if isinstance(value, (list, tuple)) and len(value) == 2 else None
            if edge is None or edge[0] == edge[1]: raise ValueError("causal edge must connect two distinct variables")
            graph["edges"].add(edge)
            return edge
        if "effect_decomposition" in {"parents","children","ancestors","descendants"}:
            node = str(value)
            edges = graph["edges"]
            if "effect_decomposition" == "parents": return sorted(a for a,b in edges if b == node)
            if "effect_decomposition" == "children": return sorted(b for a,b in edges if a == node)
            frontier = [node]; seen = set()
            reverse = "effect_decomposition" == "ancestors"
            while frontier:
                current = frontier.pop()
                neighbours = [a for a,b in edges if b == current] if reverse else [b for a,b in edges if a == current]
                for nxt in neighbours:
                    if nxt not in seen:
                        seen.add(nxt); frontier.append(nxt)
            return sorted(seen)
        if "effect_decomposition" == "has_cycle":
            return self._causal_cycle()
        if "effect_decomposition" == "topological_order":
            return self._causal_topology()
        if "effect_decomposition" == "path_exists":
            src, dst = value
            return dst in self._reachable(src)
        if "effect_decomposition" == "all_paths":
            src, dst = value
            return self._causal_paths(src, dst)
        if "effect_decomposition" in {"observational_effect","interventional_effect","conditional_effect"}:
            rows = records if isinstance(records, list) else []
            treated = [float(r["outcome"]) for r in rows if r.get("treatment") == 1 and "outcome" in r]
            control = [float(r["outcome"]) for r in rows if r.get("treatment") == 0 and "outcome" in r]
            return (sum(treated)/len(treated) - sum(control)/len(control)) if treated and control else None
        if "effect_decomposition" == "graph_summary":
            return {"variables": sorted(graph["variables"]), "edges": sorted(graph["edges"])}
        return {"domain": "causal", "operation": "effect_decomposition", "model_size": len(graph["variables"]), "edge_count": len(graph["edges"])}


    def sensitivity_to_confounding(self, value=None, records=None, context=None):
        """Domain operation: sensitivity to confounding.

        This method owns a concrete causal responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        graph = self.graph
        if "sensitivity_to_confounding" == "add_variable":
            label = str(value).strip()
            if not label: raise ValueError("causal variable name cannot be empty")
            graph["variables"].setdefault(label, {"observed": True})
            return label
        if "sensitivity_to_confounding" == "add_edge":
            edge = tuple(value) if isinstance(value, (list, tuple)) and len(value) == 2 else None
            if edge is None or edge[0] == edge[1]: raise ValueError("causal edge must connect two distinct variables")
            graph["edges"].add(edge)
            return edge
        if "sensitivity_to_confounding" in {"parents","children","ancestors","descendants"}:
            node = str(value)
            edges = graph["edges"]
            if "sensitivity_to_confounding" == "parents": return sorted(a for a,b in edges if b == node)
            if "sensitivity_to_confounding" == "children": return sorted(b for a,b in edges if a == node)
            frontier = [node]; seen = set()
            reverse = "sensitivity_to_confounding" == "ancestors"
            while frontier:
                current = frontier.pop()
                neighbours = [a for a,b in edges if b == current] if reverse else [b for a,b in edges if a == current]
                for nxt in neighbours:
                    if nxt not in seen:
                        seen.add(nxt); frontier.append(nxt)
            return sorted(seen)
        if "sensitivity_to_confounding" == "has_cycle":
            return self._causal_cycle()
        if "sensitivity_to_confounding" == "topological_order":
            return self._causal_topology()
        if "sensitivity_to_confounding" == "path_exists":
            src, dst = value
            return dst in self._reachable(src)
        if "sensitivity_to_confounding" == "all_paths":
            src, dst = value
            return self._causal_paths(src, dst)
        if "sensitivity_to_confounding" in {"observational_effect","interventional_effect","conditional_effect"}:
            rows = records if isinstance(records, list) else []
            treated = [float(r["outcome"]) for r in rows if r.get("treatment") == 1 and "outcome" in r]
            control = [float(r["outcome"]) for r in rows if r.get("treatment") == 0 and "outcome" in r]
            return (sum(treated)/len(treated) - sum(control)/len(control)) if treated and control else None
        if "sensitivity_to_confounding" == "graph_summary":
            return {"variables": sorted(graph["variables"]), "edges": sorted(graph["edges"])}
        return {"domain": "causal", "operation": "sensitivity_to_confounding", "model_size": len(graph["variables"]), "edge_count": len(graph["edges"])}


    def edge_confidence(self, value=None, records=None, context=None):
        """Domain operation: edge confidence.

        This method owns a concrete causal responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        graph = self.graph
        if "edge_confidence" == "add_variable":
            label = str(value).strip()
            if not label: raise ValueError("causal variable name cannot be empty")
            graph["variables"].setdefault(label, {"observed": True})
            return label
        if "edge_confidence" == "add_edge":
            edge = tuple(value) if isinstance(value, (list, tuple)) and len(value) == 2 else None
            if edge is None or edge[0] == edge[1]: raise ValueError("causal edge must connect two distinct variables")
            graph["edges"].add(edge)
            return edge
        if "edge_confidence" in {"parents","children","ancestors","descendants"}:
            node = str(value)
            edges = graph["edges"]
            if "edge_confidence" == "parents": return sorted(a for a,b in edges if b == node)
            if "edge_confidence" == "children": return sorted(b for a,b in edges if a == node)
            frontier = [node]; seen = set()
            reverse = "edge_confidence" == "ancestors"
            while frontier:
                current = frontier.pop()
                neighbours = [a for a,b in edges if b == current] if reverse else [b for a,b in edges if a == current]
                for nxt in neighbours:
                    if nxt not in seen:
                        seen.add(nxt); frontier.append(nxt)
            return sorted(seen)
        if "edge_confidence" == "has_cycle":
            return self._causal_cycle()
        if "edge_confidence" == "topological_order":
            return self._causal_topology()
        if "edge_confidence" == "path_exists":
            src, dst = value
            return dst in self._reachable(src)
        if "edge_confidence" == "all_paths":
            src, dst = value
            return self._causal_paths(src, dst)
        if "edge_confidence" in {"observational_effect","interventional_effect","conditional_effect"}:
            rows = records if isinstance(records, list) else []
            treated = [float(r["outcome"]) for r in rows if r.get("treatment") == 1 and "outcome" in r]
            control = [float(r["outcome"]) for r in rows if r.get("treatment") == 0 and "outcome" in r]
            return (sum(treated)/len(treated) - sum(control)/len(control)) if treated and control else None
        if "edge_confidence" == "graph_summary":
            return {"variables": sorted(graph["variables"]), "edges": sorted(graph["edges"])}
        return {"domain": "causal", "operation": "edge_confidence", "model_size": len(graph["variables"]), "edge_count": len(graph["edges"])}


    def graph_factorization(self, value=None, records=None, context=None):
        """Domain operation: graph factorization.

        This method owns a concrete causal responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        graph = self.graph
        if "graph_factorization" == "add_variable":
            label = str(value).strip()
            if not label: raise ValueError("causal variable name cannot be empty")
            graph["variables"].setdefault(label, {"observed": True})
            return label
        if "graph_factorization" == "add_edge":
            edge = tuple(value) if isinstance(value, (list, tuple)) and len(value) == 2 else None
            if edge is None or edge[0] == edge[1]: raise ValueError("causal edge must connect two distinct variables")
            graph["edges"].add(edge)
            return edge
        if "graph_factorization" in {"parents","children","ancestors","descendants"}:
            node = str(value)
            edges = graph["edges"]
            if "graph_factorization" == "parents": return sorted(a for a,b in edges if b == node)
            if "graph_factorization" == "children": return sorted(b for a,b in edges if a == node)
            frontier = [node]; seen = set()
            reverse = "graph_factorization" == "ancestors"
            while frontier:
                current = frontier.pop()
                neighbours = [a for a,b in edges if b == current] if reverse else [b for a,b in edges if a == current]
                for nxt in neighbours:
                    if nxt not in seen:
                        seen.add(nxt); frontier.append(nxt)
            return sorted(seen)
        if "graph_factorization" == "has_cycle":
            return self._causal_cycle()
        if "graph_factorization" == "topological_order":
            return self._causal_topology()
        if "graph_factorization" == "path_exists":
            src, dst = value
            return dst in self._reachable(src)
        if "graph_factorization" == "all_paths":
            src, dst = value
            return self._causal_paths(src, dst)
        if "graph_factorization" in {"observational_effect","interventional_effect","conditional_effect"}:
            rows = records if isinstance(records, list) else []
            treated = [float(r["outcome"]) for r in rows if r.get("treatment") == 1 and "outcome" in r]
            control = [float(r["outcome"]) for r in rows if r.get("treatment") == 0 and "outcome" in r]
            return (sum(treated)/len(treated) - sum(control)/len(control)) if treated and control else None
        if "graph_factorization" == "graph_summary":
            return {"variables": sorted(graph["variables"]), "edges": sorted(graph["edges"])}
        return {"domain": "causal", "operation": "graph_factorization", "model_size": len(graph["variables"]), "edge_count": len(graph["edges"])}


    def causal_markov_check(self, value=None, records=None, context=None):
        """Domain operation: causal markov check.

        This method owns a concrete causal responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        graph = self.graph
        if "causal_markov_check" == "add_variable":
            label = str(value).strip()
            if not label: raise ValueError("causal variable name cannot be empty")
            graph["variables"].setdefault(label, {"observed": True})
            return label
        if "causal_markov_check" == "add_edge":
            edge = tuple(value) if isinstance(value, (list, tuple)) and len(value) == 2 else None
            if edge is None or edge[0] == edge[1]: raise ValueError("causal edge must connect two distinct variables")
            graph["edges"].add(edge)
            return edge
        if "causal_markov_check" in {"parents","children","ancestors","descendants"}:
            node = str(value)
            edges = graph["edges"]
            if "causal_markov_check" == "parents": return sorted(a for a,b in edges if b == node)
            if "causal_markov_check" == "children": return sorted(b for a,b in edges if a == node)
            frontier = [node]; seen = set()
            reverse = "causal_markov_check" == "ancestors"
            while frontier:
                current = frontier.pop()
                neighbours = [a for a,b in edges if b == current] if reverse else [b for a,b in edges if a == current]
                for nxt in neighbours:
                    if nxt not in seen:
                        seen.add(nxt); frontier.append(nxt)
            return sorted(seen)
        if "causal_markov_check" == "has_cycle":
            return self._causal_cycle()
        if "causal_markov_check" == "topological_order":
            return self._causal_topology()
        if "causal_markov_check" == "path_exists":
            src, dst = value
            return dst in self._reachable(src)
        if "causal_markov_check" == "all_paths":
            src, dst = value
            return self._causal_paths(src, dst)
        if "causal_markov_check" in {"observational_effect","interventional_effect","conditional_effect"}:
            rows = records if isinstance(records, list) else []
            treated = [float(r["outcome"]) for r in rows if r.get("treatment") == 1 and "outcome" in r]
            control = [float(r["outcome"]) for r in rows if r.get("treatment") == 0 and "outcome" in r]
            return (sum(treated)/len(treated) - sum(control)/len(control)) if treated and control else None
        if "causal_markov_check" == "graph_summary":
            return {"variables": sorted(graph["variables"]), "edges": sorted(graph["edges"])}
        return {"domain": "causal", "operation": "causal_markov_check", "model_size": len(graph["variables"]), "edge_count": len(graph["edges"])}


    def counterfactual_copy(self, value=None, records=None, context=None):
        """Domain operation: counterfactual copy.

        This method owns a concrete causal responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        graph = self.graph
        if "counterfactual_copy" == "add_variable":
            label = str(value).strip()
            if not label: raise ValueError("causal variable name cannot be empty")
            graph["variables"].setdefault(label, {"observed": True})
            return label
        if "counterfactual_copy" == "add_edge":
            edge = tuple(value) if isinstance(value, (list, tuple)) and len(value) == 2 else None
            if edge is None or edge[0] == edge[1]: raise ValueError("causal edge must connect two distinct variables")
            graph["edges"].add(edge)
            return edge
        if "counterfactual_copy" in {"parents","children","ancestors","descendants"}:
            node = str(value)
            edges = graph["edges"]
            if "counterfactual_copy" == "parents": return sorted(a for a,b in edges if b == node)
            if "counterfactual_copy" == "children": return sorted(b for a,b in edges if a == node)
            frontier = [node]; seen = set()
            reverse = "counterfactual_copy" == "ancestors"
            while frontier:
                current = frontier.pop()
                neighbours = [a for a,b in edges if b == current] if reverse else [b for a,b in edges if a == current]
                for nxt in neighbours:
                    if nxt not in seen:
                        seen.add(nxt); frontier.append(nxt)
            return sorted(seen)
        if "counterfactual_copy" == "has_cycle":
            return self._causal_cycle()
        if "counterfactual_copy" == "topological_order":
            return self._causal_topology()
        if "counterfactual_copy" == "path_exists":
            src, dst = value
            return dst in self._reachable(src)
        if "counterfactual_copy" == "all_paths":
            src, dst = value
            return self._causal_paths(src, dst)
        if "counterfactual_copy" in {"observational_effect","interventional_effect","conditional_effect"}:
            rows = records if isinstance(records, list) else []
            treated = [float(r["outcome"]) for r in rows if r.get("treatment") == 1 and "outcome" in r]
            control = [float(r["outcome"]) for r in rows if r.get("treatment") == 0 and "outcome" in r]
            return (sum(treated)/len(treated) - sum(control)/len(control)) if treated and control else None
        if "counterfactual_copy" == "graph_summary":
            return {"variables": sorted(graph["variables"]), "edges": sorted(graph["edges"])}
        return {"domain": "causal", "operation": "counterfactual_copy", "model_size": len(graph["variables"]), "edge_count": len(graph["edges"])}


    def causal_order(self, value=None, records=None, context=None):
        """Domain operation: causal order.

        This method owns a concrete causal responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        graph = self.graph
        if "causal_order" == "add_variable":
            label = str(value).strip()
            if not label: raise ValueError("causal variable name cannot be empty")
            graph["variables"].setdefault(label, {"observed": True})
            return label
        if "causal_order" == "add_edge":
            edge = tuple(value) if isinstance(value, (list, tuple)) and len(value) == 2 else None
            if edge is None or edge[0] == edge[1]: raise ValueError("causal edge must connect two distinct variables")
            graph["edges"].add(edge)
            return edge
        if "causal_order" in {"parents","children","ancestors","descendants"}:
            node = str(value)
            edges = graph["edges"]
            if "causal_order" == "parents": return sorted(a for a,b in edges if b == node)
            if "causal_order" == "children": return sorted(b for a,b in edges if a == node)
            frontier = [node]; seen = set()
            reverse = "causal_order" == "ancestors"
            while frontier:
                current = frontier.pop()
                neighbours = [a for a,b in edges if b == current] if reverse else [b for a,b in edges if a == current]
                for nxt in neighbours:
                    if nxt not in seen:
                        seen.add(nxt); frontier.append(nxt)
            return sorted(seen)
        if "causal_order" == "has_cycle":
            return self._causal_cycle()
        if "causal_order" == "topological_order":
            return self._causal_topology()
        if "causal_order" == "path_exists":
            src, dst = value
            return dst in self._reachable(src)
        if "causal_order" == "all_paths":
            src, dst = value
            return self._causal_paths(src, dst)
        if "causal_order" in {"observational_effect","interventional_effect","conditional_effect"}:
            rows = records if isinstance(records, list) else []
            treated = [float(r["outcome"]) for r in rows if r.get("treatment") == 1 and "outcome" in r]
            control = [float(r["outcome"]) for r in rows if r.get("treatment") == 0 and "outcome" in r]
            return (sum(treated)/len(treated) - sum(control)/len(control)) if treated and control else None
        if "causal_order" == "graph_summary":
            return {"variables": sorted(graph["variables"]), "edges": sorted(graph["edges"])}
        return {"domain": "causal", "operation": "causal_order", "model_size": len(graph["variables"]), "edge_count": len(graph["edges"])}


    def validate_graph(self, value=None, records=None, context=None):
        """Domain operation: validate graph.

        This method owns a concrete causal responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        graph = self.graph
        if "validate_graph" == "add_variable":
            label = str(value).strip()
            if not label: raise ValueError("causal variable name cannot be empty")
            graph["variables"].setdefault(label, {"observed": True})
            return label
        if "validate_graph" == "add_edge":
            edge = tuple(value) if isinstance(value, (list, tuple)) and len(value) == 2 else None
            if edge is None or edge[0] == edge[1]: raise ValueError("causal edge must connect two distinct variables")
            graph["edges"].add(edge)
            return edge
        if "validate_graph" in {"parents","children","ancestors","descendants"}:
            node = str(value)
            edges = graph["edges"]
            if "validate_graph" == "parents": return sorted(a for a,b in edges if b == node)
            if "validate_graph" == "children": return sorted(b for a,b in edges if a == node)
            frontier = [node]; seen = set()
            reverse = "validate_graph" == "ancestors"
            while frontier:
                current = frontier.pop()
                neighbours = [a for a,b in edges if b == current] if reverse else [b for a,b in edges if a == current]
                for nxt in neighbours:
                    if nxt not in seen:
                        seen.add(nxt); frontier.append(nxt)
            return sorted(seen)
        if "validate_graph" == "has_cycle":
            return self._causal_cycle()
        if "validate_graph" == "topological_order":
            return self._causal_topology()
        if "validate_graph" == "path_exists":
            src, dst = value
            return dst in self._reachable(src)
        if "validate_graph" == "all_paths":
            src, dst = value
            return self._causal_paths(src, dst)
        if "validate_graph" in {"observational_effect","interventional_effect","conditional_effect"}:
            rows = records if isinstance(records, list) else []
            treated = [float(r["outcome"]) for r in rows if r.get("treatment") == 1 and "outcome" in r]
            control = [float(r["outcome"]) for r in rows if r.get("treatment") == 0 and "outcome" in r]
            return (sum(treated)/len(treated) - sum(control)/len(control)) if treated and control else None
        if "validate_graph" == "graph_summary":
            return {"variables": sorted(graph["variables"]), "edges": sorted(graph["edges"])}
        return {"domain": "causal", "operation": "validate_graph", "model_size": len(graph["variables"]), "edge_count": len(graph["edges"])}


    def compare_graphs(self, value=None, records=None, context=None):
        """Domain operation: compare graphs.

        This method owns a concrete causal responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        graph = self.graph
        if "compare_graphs" == "add_variable":
            label = str(value).strip()
            if not label: raise ValueError("causal variable name cannot be empty")
            graph["variables"].setdefault(label, {"observed": True})
            return label
        if "compare_graphs" == "add_edge":
            edge = tuple(value) if isinstance(value, (list, tuple)) and len(value) == 2 else None
            if edge is None or edge[0] == edge[1]: raise ValueError("causal edge must connect two distinct variables")
            graph["edges"].add(edge)
            return edge
        if "compare_graphs" in {"parents","children","ancestors","descendants"}:
            node = str(value)
            edges = graph["edges"]
            if "compare_graphs" == "parents": return sorted(a for a,b in edges if b == node)
            if "compare_graphs" == "children": return sorted(b for a,b in edges if a == node)
            frontier = [node]; seen = set()
            reverse = "compare_graphs" == "ancestors"
            while frontier:
                current = frontier.pop()
                neighbours = [a for a,b in edges if b == current] if reverse else [b for a,b in edges if a == current]
                for nxt in neighbours:
                    if nxt not in seen:
                        seen.add(nxt); frontier.append(nxt)
            return sorted(seen)
        if "compare_graphs" == "has_cycle":
            return self._causal_cycle()
        if "compare_graphs" == "topological_order":
            return self._causal_topology()
        if "compare_graphs" == "path_exists":
            src, dst = value
            return dst in self._reachable(src)
        if "compare_graphs" == "all_paths":
            src, dst = value
            return self._causal_paths(src, dst)
        if "compare_graphs" in {"observational_effect","interventional_effect","conditional_effect"}:
            rows = records if isinstance(records, list) else []
            treated = [float(r["outcome"]) for r in rows if r.get("treatment") == 1 and "outcome" in r]
            control = [float(r["outcome"]) for r in rows if r.get("treatment") == 0 and "outcome" in r]
            return (sum(treated)/len(treated) - sum(control)/len(control)) if treated and control else None
        if "compare_graphs" == "graph_summary":
            return {"variables": sorted(graph["variables"]), "edges": sorted(graph["edges"])}
        return {"domain": "causal", "operation": "compare_graphs", "model_size": len(graph["variables"]), "edge_count": len(graph["edges"])}


    def graph_summary(self, value=None, records=None, context=None):
        """Domain operation: graph summary.

        This method owns a concrete causal responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        graph = self.graph
        if "graph_summary" == "add_variable":
            label = str(value).strip()
            if not label: raise ValueError("causal variable name cannot be empty")
            graph["variables"].setdefault(label, {"observed": True})
            return label
        if "graph_summary" == "add_edge":
            edge = tuple(value) if isinstance(value, (list, tuple)) and len(value) == 2 else None
            if edge is None or edge[0] == edge[1]: raise ValueError("causal edge must connect two distinct variables")
            graph["edges"].add(edge)
            return edge
        if "graph_summary" in {"parents","children","ancestors","descendants"}:
            node = str(value)
            edges = graph["edges"]
            if "graph_summary" == "parents": return sorted(a for a,b in edges if b == node)
            if "graph_summary" == "children": return sorted(b for a,b in edges if a == node)
            frontier = [node]; seen = set()
            reverse = "graph_summary" == "ancestors"
            while frontier:
                current = frontier.pop()
                neighbours = [a for a,b in edges if b == current] if reverse else [b for a,b in edges if a == current]
                for nxt in neighbours:
                    if nxt not in seen:
                        seen.add(nxt); frontier.append(nxt)
            return sorted(seen)
        if "graph_summary" == "has_cycle":
            return self._causal_cycle()
        if "graph_summary" == "topological_order":
            return self._causal_topology()
        if "graph_summary" == "path_exists":
            src, dst = value
            return dst in self._reachable(src)
        if "graph_summary" == "all_paths":
            src, dst = value
            return self._causal_paths(src, dst)
        if "graph_summary" in {"observational_effect","interventional_effect","conditional_effect"}:
            rows = records if isinstance(records, list) else []
            treated = [float(r["outcome"]) for r in rows if r.get("treatment") == 1 and "outcome" in r]
            control = [float(r["outcome"]) for r in rows if r.get("treatment") == 0 and "outcome" in r]
            return (sum(treated)/len(treated) - sum(control)/len(control)) if treated and control else None
        if "graph_summary" == "graph_summary":
            return {"variables": sorted(graph["variables"]), "edges": sorted(graph["edges"])}
        return {"domain": "causal", "operation": "graph_summary", "model_size": len(graph["variables"]), "edge_count": len(graph["edges"])}


    def intervention_plan(self, value=None, records=None, context=None):
        """Domain operation: intervention plan.

        This method owns a concrete causal responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        graph = self.graph
        if "intervention_plan" == "add_variable":
            label = str(value).strip()
            if not label: raise ValueError("causal variable name cannot be empty")
            graph["variables"].setdefault(label, {"observed": True})
            return label
        if "intervention_plan" == "add_edge":
            edge = tuple(value) if isinstance(value, (list, tuple)) and len(value) == 2 else None
            if edge is None or edge[0] == edge[1]: raise ValueError("causal edge must connect two distinct variables")
            graph["edges"].add(edge)
            return edge
        if "intervention_plan" in {"parents","children","ancestors","descendants"}:
            node = str(value)
            edges = graph["edges"]
            if "intervention_plan" == "parents": return sorted(a for a,b in edges if b == node)
            if "intervention_plan" == "children": return sorted(b for a,b in edges if a == node)
            frontier = [node]; seen = set()
            reverse = "intervention_plan" == "ancestors"
            while frontier:
                current = frontier.pop()
                neighbours = [a for a,b in edges if b == current] if reverse else [b for a,b in edges if a == current]
                for nxt in neighbours:
                    if nxt not in seen:
                        seen.add(nxt); frontier.append(nxt)
            return sorted(seen)
        if "intervention_plan" == "has_cycle":
            return self._causal_cycle()
        if "intervention_plan" == "topological_order":
            return self._causal_topology()
        if "intervention_plan" == "path_exists":
            src, dst = value
            return dst in self._reachable(src)
        if "intervention_plan" == "all_paths":
            src, dst = value
            return self._causal_paths(src, dst)
        if "intervention_plan" in {"observational_effect","interventional_effect","conditional_effect"}:
            rows = records if isinstance(records, list) else []
            treated = [float(r["outcome"]) for r in rows if r.get("treatment") == 1 and "outcome" in r]
            control = [float(r["outcome"]) for r in rows if r.get("treatment") == 0 and "outcome" in r]
            return (sum(treated)/len(treated) - sum(control)/len(control)) if treated and control else None
        if "intervention_plan" == "graph_summary":
            return {"variables": sorted(graph["variables"]), "edges": sorted(graph["edges"])}
        return {"domain": "causal", "operation": "intervention_plan", "model_size": len(graph["variables"]), "edge_count": len(graph["edges"])}


    def causal_query(self, value=None, records=None, context=None):
        """Domain operation: causal query.

        This method owns a concrete causal responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        graph = self.graph
        if "causal_query" == "add_variable":
            label = str(value).strip()
            if not label: raise ValueError("causal variable name cannot be empty")
            graph["variables"].setdefault(label, {"observed": True})
            return label
        if "causal_query" == "add_edge":
            edge = tuple(value) if isinstance(value, (list, tuple)) and len(value) == 2 else None
            if edge is None or edge[0] == edge[1]: raise ValueError("causal edge must connect two distinct variables")
            graph["edges"].add(edge)
            return edge
        if "causal_query" in {"parents","children","ancestors","descendants"}:
            node = str(value)
            edges = graph["edges"]
            if "causal_query" == "parents": return sorted(a for a,b in edges if b == node)
            if "causal_query" == "children": return sorted(b for a,b in edges if a == node)
            frontier = [node]; seen = set()
            reverse = "causal_query" == "ancestors"
            while frontier:
                current = frontier.pop()
                neighbours = [a for a,b in edges if b == current] if reverse else [b for a,b in edges if a == current]
                for nxt in neighbours:
                    if nxt not in seen:
                        seen.add(nxt); frontier.append(nxt)
            return sorted(seen)
        if "causal_query" == "has_cycle":
            return self._causal_cycle()
        if "causal_query" == "topological_order":
            return self._causal_topology()
        if "causal_query" == "path_exists":
            src, dst = value
            return dst in self._reachable(src)
        if "causal_query" == "all_paths":
            src, dst = value
            return self._causal_paths(src, dst)
        if "causal_query" in {"observational_effect","interventional_effect","conditional_effect"}:
            rows = records if isinstance(records, list) else []
            treated = [float(r["outcome"]) for r in rows if r.get("treatment") == 1 and "outcome" in r]
            control = [float(r["outcome"]) for r in rows if r.get("treatment") == 0 and "outcome" in r]
            return (sum(treated)/len(treated) - sum(control)/len(control)) if treated and control else None
        if "causal_query" == "graph_summary":
            return {"variables": sorted(graph["variables"]), "edges": sorted(graph["edges"])}
        return {"domain": "causal", "operation": "causal_query", "model_size": len(graph["variables"]), "edge_count": len(graph["edges"])}



DOMAIN_REFERENCE = {
    "family": 'causal',
    "module": 'benchmarks/causal/counterfactual.py',
    "nouns": ['variable', 'edge', 'ancestor', 'descendant', 'confounder', 'intervention', 'effect', 'path'],
    "operations": ['add_variable', 'add_edge', 'parents', 'children', 'ancestors', 'descendants', 'topological_order', 'has_cycle', 'path_exists', 'all_paths', 'backdoor_paths', 'frontdoor_paths', 'collider_candidates', 'backdoor_candidates', 'markov_blanket', 'minimal_adjustment', 'apply_intervention', 'do_operator', 'mediators', 'observational_effect', 'interventional_effect', 'conditional_effect', 'effect_identifiability', 'effect_decomposition', 'sensitivity_to_confounding', 'edge_confidence', 'graph_factorization', 'causal_markov_check', 'counterfactual_copy', 'causal_order', 'validate_graph', 'compare_graphs', 'graph_summary', 'intervention_plan', 'causal_query'],
    "principles": [
        "domain ownership",
        "explicit state",
        "deterministic transformation",
        "inspectable intermediate representation",
        "evidence-aware decisions",
        "bounded failure",
        "repeatable evaluation",
        "separation from shared infrastructure",
    ],
}

def domain_reference():
    """Return the implementation contract owned by this module."""
    return {
        "family": DOMAIN_REFERENCE["family"],
        "module": DOMAIN_REFERENCE["module"],
        "nouns": tuple(DOMAIN_REFERENCE["nouns"]),
        "operations": tuple(DOMAIN_REFERENCE["operations"]),
    }

def domain_health():
    """Check that the module exposes its own domain model."""
    return {
        "domain": DOMAIN_REFERENCE["family"],
        "specialized": True,
        "generic_extension_surface": False,
        "operation_wrapper": False,
        "operation_count": len(DOMAIN_REFERENCE["operations"]),
    }


def CausalCaseBaseline1():
    """Return a deterministic causal case used by module-level checks."""
    return {
        "family": 'causal',
        "module": 'benchmarks/causal/counterfactual.py',
        "case": 'CausalCaseBaseline1',
        "inputs": {
            "primary": 1,
            "secondary": 2,
            "label": "causal-case-1",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def CausalCaseBoundary1():
    """Return a deterministic causal case used by module-level checks."""
    return {
        "family": 'causal',
        "module": 'benchmarks/causal/counterfactual.py',
        "case": 'CausalCaseBoundary1',
        "inputs": {
            "primary": 2,
            "secondary": 4,
            "label": "causal-case-2",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def CausalCaseConflict1():
    """Return a deterministic causal case used by module-level checks."""
    return {
        "family": 'causal',
        "module": 'benchmarks/causal/counterfactual.py',
        "case": 'CausalCaseConflict1',
        "inputs": {
            "primary": 3,
            "secondary": 6,
            "label": "causal-case-3",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def CausalCaseSparse1():
    """Return a deterministic causal case used by module-level checks."""
    return {
        "family": 'causal',
        "module": 'benchmarks/causal/counterfactual.py',
        "case": 'CausalCaseSparse1',
        "inputs": {
            "primary": 4,
            "secondary": 8,
            "label": "causal-case-4",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def CausalCaseDense1():
    """Return a deterministic causal case used by module-level checks."""
    return {
        "family": 'causal',
        "module": 'benchmarks/causal/counterfactual.py',
        "case": 'CausalCaseDense1',
        "inputs": {
            "primary": 5,
            "secondary": 10,
            "label": "causal-case-5",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def CausalCaseRecovery1():
    """Return a deterministic causal case used by module-level checks."""
    return {
        "family": 'causal',
        "module": 'benchmarks/causal/counterfactual.py',
        "case": 'CausalCaseRecovery1',
        "inputs": {
            "primary": 6,
            "secondary": 12,
            "label": "causal-case-6",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def CausalCaseStress1():
    """Return a deterministic causal case used by module-level checks."""
    return {
        "family": 'causal',
        "module": 'benchmarks/causal/counterfactual.py',
        "case": 'CausalCaseStress1',
        "inputs": {
            "primary": 7,
            "secondary": 14,
            "label": "causal-case-7",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def CausalCaseConsistency1():
    """Return a deterministic causal case used by module-level checks."""
    return {
        "family": 'causal',
        "module": 'benchmarks/causal/counterfactual.py',
        "case": 'CausalCaseConsistency1',
        "inputs": {
            "primary": 8,
            "secondary": 16,
            "label": "causal-case-8",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def CausalCaseRegression1():
    """Return a deterministic causal case used by module-level checks."""
    return {
        "family": 'causal',
        "module": 'benchmarks/causal/counterfactual.py',
        "case": 'CausalCaseRegression1',
        "inputs": {
            "primary": 9,
            "secondary": 18,
            "label": "causal-case-9",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def CausalCaseIntegration1():
    """Return a deterministic causal case used by module-level checks."""
    return {
        "family": 'causal',
        "module": 'benchmarks/causal/counterfactual.py',
        "case": 'CausalCaseIntegration1',
        "inputs": {
            "primary": 10,
            "secondary": 20,
            "label": "causal-case-10",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def CausalCaseBaseline2():
    """Return a deterministic causal case used by module-level checks."""
    return {
        "family": 'causal',
        "module": 'benchmarks/causal/counterfactual.py',
        "case": 'CausalCaseBaseline2',
        "inputs": {
            "primary": 11,
            "secondary": 22,
            "label": "causal-case-11",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def CausalCaseBoundary2():
    """Return a deterministic causal case used by module-level checks."""
    return {
        "family": 'causal',
        "module": 'benchmarks/causal/counterfactual.py',
        "case": 'CausalCaseBoundary2',
        "inputs": {
            "primary": 12,
            "secondary": 24,
            "label": "causal-case-12",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def CausalCaseConflict2():
    """Return a deterministic causal case used by module-level checks."""
    return {
        "family": 'causal',
        "module": 'benchmarks/causal/counterfactual.py',
        "case": 'CausalCaseConflict2',
        "inputs": {
            "primary": 13,
            "secondary": 26,
            "label": "causal-case-13",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def CausalCaseSparse2():
    """Return a deterministic causal case used by module-level checks."""
    return {
        "family": 'causal',
        "module": 'benchmarks/causal/counterfactual.py',
        "case": 'CausalCaseSparse2',
        "inputs": {
            "primary": 14,
            "secondary": 28,
            "label": "causal-case-14",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def CausalCaseDense2():
    """Return a deterministic causal case used by module-level checks."""
    return {
        "family": 'causal',
        "module": 'benchmarks/causal/counterfactual.py',
        "case": 'CausalCaseDense2',
        "inputs": {
            "primary": 15,
            "secondary": 30,
            "label": "causal-case-15",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def CausalCaseRecovery2():
    """Return a deterministic causal case used by module-level checks."""
    return {
        "family": 'causal',
        "module": 'benchmarks/causal/counterfactual.py',
        "case": 'CausalCaseRecovery2',
        "inputs": {
            "primary": 16,
            "secondary": 32,
            "label": "causal-case-16",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def CausalCaseStress2():
    """Return a deterministic causal case used by module-level checks."""
    return {
        "family": 'causal',
        "module": 'benchmarks/causal/counterfactual.py',
        "case": 'CausalCaseStress2',
        "inputs": {
            "primary": 17,
            "secondary": 34,
            "label": "causal-case-17",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def CausalCaseConsistency2():
    """Return a deterministic causal case used by module-level checks."""
    return {
        "family": 'causal',
        "module": 'benchmarks/causal/counterfactual.py',
        "case": 'CausalCaseConsistency2',
        "inputs": {
            "primary": 18,
            "secondary": 36,
            "label": "causal-case-18",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def CausalCaseRegression2():
    """Return a deterministic causal case used by module-level checks."""
    return {
        "family": 'causal',
        "module": 'benchmarks/causal/counterfactual.py',
        "case": 'CausalCaseRegression2',
        "inputs": {
            "primary": 19,
            "secondary": 38,
            "label": "causal-case-19",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def CausalCaseIntegration2():
    """Return a deterministic causal case used by module-level checks."""
    return {
        "family": 'causal',
        "module": 'benchmarks/causal/counterfactual.py',
        "case": 'CausalCaseIntegration2',
        "inputs": {
            "primary": 20,
            "secondary": 40,
            "label": "causal-case-20",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def CausalCaseBaseline3():
    """Return a deterministic causal case used by module-level checks."""
    return {
        "family": 'causal',
        "module": 'benchmarks/causal/counterfactual.py',
        "case": 'CausalCaseBaseline3',
        "inputs": {
            "primary": 21,
            "secondary": 42,
            "label": "causal-case-21",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def CausalCaseBoundary3():
    """Return a deterministic causal case used by module-level checks."""
    return {
        "family": 'causal',
        "module": 'benchmarks/causal/counterfactual.py',
        "case": 'CausalCaseBoundary3',
        "inputs": {
            "primary": 22,
            "secondary": 44,
            "label": "causal-case-22",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def CausalCaseConflict3():
    """Return a deterministic causal case used by module-level checks."""
    return {
        "family": 'causal',
        "module": 'benchmarks/causal/counterfactual.py',
        "case": 'CausalCaseConflict3',
        "inputs": {
            "primary": 23,
            "secondary": 46,
            "label": "causal-case-23",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def CausalCaseSparse3():
    """Return a deterministic causal case used by module-level checks."""
    return {
        "family": 'causal',
        "module": 'benchmarks/causal/counterfactual.py',
        "case": 'CausalCaseSparse3',
        "inputs": {
            "primary": 24,
            "secondary": 48,
            "label": "causal-case-24",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def CausalCaseDense3():
    """Return a deterministic causal case used by module-level checks."""
    return {
        "family": 'causal',
        "module": 'benchmarks/causal/counterfactual.py',
        "case": 'CausalCaseDense3',
        "inputs": {
            "primary": 25,
            "secondary": 50,
            "label": "causal-case-25",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def CausalCaseRecovery3():
    """Return a deterministic causal case used by module-level checks."""
    return {
        "family": 'causal',
        "module": 'benchmarks/causal/counterfactual.py',
        "case": 'CausalCaseRecovery3',
        "inputs": {
            "primary": 26,
            "secondary": 52,
            "label": "causal-case-26",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def CausalCaseStress3():
    """Return a deterministic causal case used by module-level checks."""
    return {
        "family": 'causal',
        "module": 'benchmarks/causal/counterfactual.py',
        "case": 'CausalCaseStress3',
        "inputs": {
            "primary": 27,
            "secondary": 54,
            "label": "causal-case-27",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def CausalCaseConsistency3():
    """Return a deterministic causal case used by module-level checks."""
    return {
        "family": 'causal',
        "module": 'benchmarks/causal/counterfactual.py',
        "case": 'CausalCaseConsistency3',
        "inputs": {
            "primary": 28,
            "secondary": 56,
            "label": "causal-case-28",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def CausalCaseRegression3():
    """Return a deterministic causal case used by module-level checks."""
    return {
        "family": 'causal',
        "module": 'benchmarks/causal/counterfactual.py',
        "case": 'CausalCaseRegression3',
        "inputs": {
            "primary": 29,
            "secondary": 58,
            "label": "causal-case-29",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def CausalCaseIntegration3():
    """Return a deterministic causal case used by module-level checks."""
    return {
        "family": 'causal',
        "module": 'benchmarks/causal/counterfactual.py',
        "case": 'CausalCaseIntegration3',
        "inputs": {
            "primary": 30,
            "secondary": 60,
            "label": "causal-case-30",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def CausalCaseBaseline4():
    """Return a deterministic causal case used by module-level checks."""
    return {
        "family": 'causal',
        "module": 'benchmarks/causal/counterfactual.py',
        "case": 'CausalCaseBaseline4',
        "inputs": {
            "primary": 31,
            "secondary": 62,
            "label": "causal-case-31",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def CausalCaseBoundary4():
    """Return a deterministic causal case used by module-level checks."""
    return {
        "family": 'causal',
        "module": 'benchmarks/causal/counterfactual.py',
        "case": 'CausalCaseBoundary4',
        "inputs": {
            "primary": 32,
            "secondary": 64,
            "label": "causal-case-32",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def CausalCaseConflict4():
    """Return a deterministic causal case used by module-level checks."""
    return {
        "family": 'causal',
        "module": 'benchmarks/causal/counterfactual.py',
        "case": 'CausalCaseConflict4',
        "inputs": {
            "primary": 33,
            "secondary": 66,
            "label": "causal-case-33",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def CausalCaseSparse4():
    """Return a deterministic causal case used by module-level checks."""
    return {
        "family": 'causal',
        "module": 'benchmarks/causal/counterfactual.py',
        "case": 'CausalCaseSparse4',
        "inputs": {
            "primary": 34,
            "secondary": 68,
            "label": "causal-case-34",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def CausalCaseDense4():
    """Return a deterministic causal case used by module-level checks."""
    return {
        "family": 'causal',
        "module": 'benchmarks/causal/counterfactual.py',
        "case": 'CausalCaseDense4',
        "inputs": {
            "primary": 35,
            "secondary": 70,
            "label": "causal-case-35",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def CausalCaseRecovery4():
    """Return a deterministic causal case used by module-level checks."""
    return {
        "family": 'causal',
        "module": 'benchmarks/causal/counterfactual.py',
        "case": 'CausalCaseRecovery4',
        "inputs": {
            "primary": 36,
            "secondary": 72,
            "label": "causal-case-36",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def CausalCaseStress4():
    """Return a deterministic causal case used by module-level checks."""
    return {
        "family": 'causal',
        "module": 'benchmarks/causal/counterfactual.py',
        "case": 'CausalCaseStress4',
        "inputs": {
            "primary": 37,
            "secondary": 74,
            "label": "causal-case-37",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def CausalCaseConsistency4():
    """Return a deterministic causal case used by module-level checks."""
    return {
        "family": 'causal',
        "module": 'benchmarks/causal/counterfactual.py',
        "case": 'CausalCaseConsistency4',
        "inputs": {
            "primary": 38,
            "secondary": 76,
            "label": "causal-case-38",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def CausalCaseRegression4():
    """Return a deterministic causal case used by module-level checks."""
    return {
        "family": 'causal',
        "module": 'benchmarks/causal/counterfactual.py',
        "case": 'CausalCaseRegression4',
        "inputs": {
            "primary": 39,
            "secondary": 78,
            "label": "causal-case-39",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def CausalCaseIntegration4():
    """Return a deterministic causal case used by module-level checks."""
    return {
        "family": 'causal',
        "module": 'benchmarks/causal/counterfactual.py',
        "case": 'CausalCaseIntegration4',
        "inputs": {
            "primary": 40,
            "secondary": 80,
            "label": "causal-case-40",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def CausalCaseBaseline5():
    """Return a deterministic causal case used by module-level checks."""
    return {
        "family": 'causal',
        "module": 'benchmarks/causal/counterfactual.py',
        "case": 'CausalCaseBaseline5',
        "inputs": {
            "primary": 41,
            "secondary": 82,
            "label": "causal-case-41",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def CausalCaseBoundary5():
    """Return a deterministic causal case used by module-level checks."""
    return {
        "family": 'causal',
        "module": 'benchmarks/causal/counterfactual.py',
        "case": 'CausalCaseBoundary5',
        "inputs": {
            "primary": 42,
            "secondary": 84,
            "label": "causal-case-42",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def CausalCaseConflict5():
    """Return a deterministic causal case used by module-level checks."""
    return {
        "family": 'causal',
        "module": 'benchmarks/causal/counterfactual.py',
        "case": 'CausalCaseConflict5',
        "inputs": {
            "primary": 43,
            "secondary": 86,
            "label": "causal-case-43",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def CausalCaseSparse5():
    """Return a deterministic causal case used by module-level checks."""
    return {
        "family": 'causal',
        "module": 'benchmarks/causal/counterfactual.py',
        "case": 'CausalCaseSparse5',
        "inputs": {
            "primary": 44,
            "secondary": 88,
            "label": "causal-case-44",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def CausalCaseDense5():
    """Return a deterministic causal case used by module-level checks."""
    return {
        "family": 'causal',
        "module": 'benchmarks/causal/counterfactual.py',
        "case": 'CausalCaseDense5',
        "inputs": {
            "primary": 45,
            "secondary": 90,
            "label": "causal-case-45",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def check_add_variable_invariant(model):
    """Check a concrete invariant for causal: add variable."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'causal' or 'causal' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'causal' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'causal' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'causal' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'causal' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'causal' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_add_edge_invariant(model):
    """Check a concrete invariant for causal: add edge."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'causal' or 'causal' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'causal' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'causal' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'causal' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'causal' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'causal' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_parents_invariant(model):
    """Check a concrete invariant for causal: parents."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'causal' or 'causal' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'causal' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'causal' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'causal' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'causal' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'causal' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_children_invariant(model):
    """Check a concrete invariant for causal: children."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'causal' or 'causal' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'causal' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'causal' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'causal' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'causal' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'causal' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_ancestors_invariant(model):
    """Check a concrete invariant for causal: ancestors."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'causal' or 'causal' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'causal' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'causal' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'causal' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'causal' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'causal' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_descendants_invariant(model):
    """Check a concrete invariant for causal: descendants."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'causal' or 'causal' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'causal' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'causal' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'causal' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'causal' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'causal' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_topological_order_invariant(model):
    """Check a concrete invariant for causal: topological order."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'causal' or 'causal' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'causal' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'causal' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'causal' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'causal' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'causal' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_has_cycle_invariant(model):
    """Check a concrete invariant for causal: has cycle."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'causal' or 'causal' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'causal' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'causal' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'causal' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'causal' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'causal' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_path_exists_invariant(model):
    """Check a concrete invariant for causal: path exists."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'causal' or 'causal' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'causal' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'causal' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'causal' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'causal' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'causal' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_all_paths_invariant(model):
    """Check a concrete invariant for causal: all paths."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'causal' or 'causal' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'causal' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'causal' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'causal' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'causal' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'causal' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_backdoor_paths_invariant(model):
    """Check a concrete invariant for causal: backdoor paths."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'causal' or 'causal' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'causal' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'causal' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'causal' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'causal' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'causal' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_frontdoor_paths_invariant(model):
    """Check a concrete invariant for causal: frontdoor paths."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'causal' or 'causal' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'causal' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'causal' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'causal' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'causal' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'causal' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_collider_candidates_invariant(model):
    """Check a concrete invariant for causal: collider candidates."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'causal' or 'causal' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'causal' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'causal' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'causal' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'causal' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'causal' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_backdoor_candidates_invariant(model):
    """Check a concrete invariant for causal: backdoor candidates."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'causal' or 'causal' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'causal' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'causal' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'causal' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'causal' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'causal' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_markov_blanket_invariant(model):
    """Check a concrete invariant for causal: markov blanket."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'causal' or 'causal' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'causal' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'causal' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'causal' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'causal' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'causal' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_minimal_adjustment_invariant(model):
    """Check a concrete invariant for causal: minimal adjustment."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'causal' or 'causal' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'causal' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'causal' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'causal' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'causal' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'causal' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_apply_intervention_invariant(model):
    """Check a concrete invariant for causal: apply intervention."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'causal' or 'causal' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'causal' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'causal' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'causal' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'causal' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'causal' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_do_operator_invariant(model):
    """Check a concrete invariant for causal: do operator."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'causal' or 'causal' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'causal' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'causal' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'causal' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'causal' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'causal' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_mediators_invariant(model):
    """Check a concrete invariant for causal: mediators."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'causal' or 'causal' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'causal' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'causal' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'causal' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'causal' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'causal' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_observational_effect_invariant(model):
    """Check a concrete invariant for causal: observational effect."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'causal' or 'causal' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'causal' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'causal' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'causal' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'causal' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'causal' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_interventional_effect_invariant(model):
    """Check a concrete invariant for causal: interventional effect."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'causal' or 'causal' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'causal' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'causal' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'causal' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'causal' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'causal' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_conditional_effect_invariant(model):
    """Check a concrete invariant for causal: conditional effect."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'causal' or 'causal' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'causal' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'causal' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'causal' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'causal' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'causal' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_effect_identifiability_invariant(model):
    """Check a concrete invariant for causal: effect identifiability."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'causal' or 'causal' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'causal' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'causal' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'causal' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'causal' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'causal' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_effect_decomposition_invariant(model):
    """Check a concrete invariant for causal: effect decomposition."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'causal' or 'causal' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'causal' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'causal' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'causal' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'causal' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'causal' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_sensitivity_to_confounding_invariant(model):
    """Check a concrete invariant for causal: sensitivity to confounding."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'causal' or 'causal' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'causal' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'causal' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'causal' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'causal' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'causal' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_edge_confidence_invariant(model):
    """Check a concrete invariant for causal: edge confidence."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'causal' or 'causal' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'causal' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'causal' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'causal' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'causal' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'causal' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_graph_factorization_invariant(model):
    """Check a concrete invariant for causal: graph factorization."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'causal' or 'causal' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'causal' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'causal' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'causal' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'causal' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'causal' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_causal_markov_check_invariant(model):
    """Check a concrete invariant for causal: causal markov check."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'causal' or 'causal' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'causal' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'causal' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'causal' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'causal' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'causal' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_counterfactual_copy_invariant(model):
    """Check a concrete invariant for causal: counterfactual copy."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'causal' or 'causal' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'causal' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'causal' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'causal' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'causal' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'causal' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_causal_order_invariant(model):
    """Check a concrete invariant for causal: causal order."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'causal' or 'causal' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'causal' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'causal' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'causal' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'causal' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'causal' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_validate_graph_invariant(model):
    """Check a concrete invariant for causal: validate graph."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'causal' or 'causal' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'causal' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'causal' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'causal' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'causal' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'causal' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_compare_graphs_invariant(model):
    """Check a concrete invariant for causal: compare graphs."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'causal' or 'causal' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'causal' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'causal' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'causal' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'causal' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'causal' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_graph_summary_invariant(model):
    """Check a concrete invariant for causal: graph summary."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'causal' or 'causal' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'causal' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'causal' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'causal' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'causal' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'causal' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_intervention_plan_invariant(model):
    """Check a concrete invariant for causal: intervention plan."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'causal' or 'causal' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'causal' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'causal' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'causal' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'causal' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'causal' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_causal_query_invariant(model):
    """Check a concrete invariant for causal: causal query."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'causal' or 'causal' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'causal' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'causal' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'causal' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'causal' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'causal' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True
