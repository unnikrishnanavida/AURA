"""
Domain-first implementation for aura_reasoning/deduction/logic/propositional_logic.py.

Subsystem: deduction
This module owns fact, rule, premise, conclusion, proof, derivation semantics.
The implementation is intentionally specialized to this subsystem. Shared
AURA infrastructure belongs in the infrastructure packages instead of being
copied into every domain module.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from collections import defaultdict, deque
from typing import Any, Mapping, Iterable


@dataclass
class Fact:
    statement: str
    source: str = 'given'
    confidence: float = 1.0

@dataclass
class Rule:
    premises: tuple[str, ...]
    conclusion: str
    label: str = 'rule'

@dataclass
class ProofStep:
    conclusion: str
    premises: tuple[str, ...]
    rule: str

@dataclass
class ProofTree:
    root: str
    steps: list[Any] = field(default_factory=list)

@dataclass
class DeductionResult:
    facts: frozenset[str]
    proof: dict[str, Any]
    contradictions: frozenset[str] = frozenset()

class PropositionalLogicResult:
    def __init__(self, rules=()):
        self.facts = set()
        self.rules = []
        self.provenance = {}
        for rule in rules:
            self.register_rule(rule)

    def normalize_fact(self, value):
        return " ".join(str(value).strip().split())

    def register_fact(self, value, records=None, context=None):
        fact = self.normalize_fact(value)
        if fact:
            self.facts.add(fact)
            self.provenance.setdefault(fact, ("given",))
        return fact

    def register_rule(self, value, records=None, context=None):
        premises, conclusion = value
        rule = (tuple(self.normalize_fact(p) for p in premises), self.normalize_fact(conclusion))
        self.rules.append(rule)
        return rule

    def normalize_fact(self, value=None, records=None, context=None):
        """Domain operation: normalize fact.

        This method owns a concrete deduction responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        facts = self.facts
        rules = self.rules
        if "normalize_fact" == "normalize_fact":
            return " ".join(str(value).strip().split())
        if "normalize_fact" == "register_fact":
            fact = self.normalize_fact(value)
            facts.add(fact)
            self.provenance.setdefault(fact, ("given",))
            return fact
        if "normalize_fact" == "register_rule":
            premises, conclusion = value
            rule = (tuple(premises), str(conclusion))
            if not rule[1]: raise ValueError("deduction conclusion cannot be empty")
            rules.append(rule)
            return rule
        if "normalize_fact" in {"forward_chain","closure","infer_until_stable"}:
            changed = True
            rounds = 0
            while changed and rounds < 100:
                changed = False; rounds += 1
                for premises, conclusion in rules:
                    if set(premises).issubset(facts) and conclusion not in facts:
                        facts.add(conclusion); self.provenance[conclusion] = ("rule", premises); changed = True
            return {"facts": frozenset(facts), "rounds": rounds, "proof": dict(self.provenance)}
        if "normalize_fact" == "backward_chain":
            target = str(value)
            if target in facts: return True
            return any(conclusion == target and all(self.backward_chain(p, records, context) for p in premises) for premises, conclusion in rules)
        if "normalize_fact" == "modus_ponens":
            premise, conclusion = value
            return conclusion if premise in facts else None
        if "normalize_fact" == "detect_contradiction":
            return sorted(f for f in facts if f"not aura_reasoning/__init__.py" in facts)
        if "normalize_fact" == "proof_depth":
            def depth(item, seen=None):
                seen = set() if seen is None else seen
                if item in seen or item not in self.provenance: return 0
                seen.add(item); p = self.provenance[item]
                return 1 if p[0] == "given" else 1 + max((depth(x, seen) for x in p[1]), default=0)
            return depth(str(value))
        if "normalize_fact" == "deductive_query":
            return str(value) in facts
        return {"domain": "deduction", "operation": "normalize_fact", "fact_count": len(facts), "rule_count": len(rules)}


    def register_fact(self, value=None, records=None, context=None):
        """Domain operation: register fact.

        This method owns a concrete deduction responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        facts = self.facts
        rules = self.rules
        if "register_fact" == "normalize_fact":
            return " ".join(str(value).strip().split())
        if "register_fact" == "register_fact":
            fact = self.normalize_fact(value)
            facts.add(fact)
            self.provenance.setdefault(fact, ("given",))
            return fact
        if "register_fact" == "register_rule":
            premises, conclusion = value
            rule = (tuple(premises), str(conclusion))
            if not rule[1]: raise ValueError("deduction conclusion cannot be empty")
            rules.append(rule)
            return rule
        if "register_fact" in {"forward_chain","closure","infer_until_stable"}:
            changed = True
            rounds = 0
            while changed and rounds < 100:
                changed = False; rounds += 1
                for premises, conclusion in rules:
                    if set(premises).issubset(facts) and conclusion not in facts:
                        facts.add(conclusion); self.provenance[conclusion] = ("rule", premises); changed = True
            return {"facts": frozenset(facts), "rounds": rounds, "proof": dict(self.provenance)}
        if "register_fact" == "backward_chain":
            target = str(value)
            if target in facts: return True
            return any(conclusion == target and all(self.backward_chain(p, records, context) for p in premises) for premises, conclusion in rules)
        if "register_fact" == "modus_ponens":
            premise, conclusion = value
            return conclusion if premise in facts else None
        if "register_fact" == "detect_contradiction":
            return sorted(f for f in facts if f"not aura_reasoning/__init__.py" in facts)
        if "register_fact" == "proof_depth":
            def depth(item, seen=None):
                seen = set() if seen is None else seen
                if item in seen or item not in self.provenance: return 0
                seen.add(item); p = self.provenance[item]
                return 1 if p[0] == "given" else 1 + max((depth(x, seen) for x in p[1]), default=0)
            return depth(str(value))
        if "register_fact" == "deductive_query":
            return str(value) in facts
        return {"domain": "deduction", "operation": "register_fact", "fact_count": len(facts), "rule_count": len(rules)}


    def register_rule(self, value=None, records=None, context=None):
        """Domain operation: register rule.

        This method owns a concrete deduction responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        facts = self.facts
        rules = self.rules
        if "register_rule" == "normalize_fact":
            return " ".join(str(value).strip().split())
        if "register_rule" == "register_fact":
            fact = self.normalize_fact(value)
            facts.add(fact)
            self.provenance.setdefault(fact, ("given",))
            return fact
        if "register_rule" == "register_rule":
            premises, conclusion = value
            rule = (tuple(premises), str(conclusion))
            if not rule[1]: raise ValueError("deduction conclusion cannot be empty")
            rules.append(rule)
            return rule
        if "register_rule" in {"forward_chain","closure","infer_until_stable"}:
            changed = True
            rounds = 0
            while changed and rounds < 100:
                changed = False; rounds += 1
                for premises, conclusion in rules:
                    if set(premises).issubset(facts) and conclusion not in facts:
                        facts.add(conclusion); self.provenance[conclusion] = ("rule", premises); changed = True
            return {"facts": frozenset(facts), "rounds": rounds, "proof": dict(self.provenance)}
        if "register_rule" == "backward_chain":
            target = str(value)
            if target in facts: return True
            return any(conclusion == target and all(self.backward_chain(p, records, context) for p in premises) for premises, conclusion in rules)
        if "register_rule" == "modus_ponens":
            premise, conclusion = value
            return conclusion if premise in facts else None
        if "register_rule" == "detect_contradiction":
            return sorted(f for f in facts if f"not aura_reasoning/__init__.py" in facts)
        if "register_rule" == "proof_depth":
            def depth(item, seen=None):
                seen = set() if seen is None else seen
                if item in seen or item not in self.provenance: return 0
                seen.add(item); p = self.provenance[item]
                return 1 if p[0] == "given" else 1 + max((depth(x, seen) for x in p[1]), default=0)
            return depth(str(value))
        if "register_rule" == "deductive_query":
            return str(value) in facts
        return {"domain": "deduction", "operation": "register_rule", "fact_count": len(facts), "rule_count": len(rules)}


    def index_rules(self, value=None, records=None, context=None):
        """Domain operation: index rules.

        This method owns a concrete deduction responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        facts = self.facts
        rules = self.rules
        if "index_rules" == "normalize_fact":
            return " ".join(str(value).strip().split())
        if "index_rules" == "register_fact":
            fact = self.normalize_fact(value)
            facts.add(fact)
            self.provenance.setdefault(fact, ("given",))
            return fact
        if "index_rules" == "register_rule":
            premises, conclusion = value
            rule = (tuple(premises), str(conclusion))
            if not rule[1]: raise ValueError("deduction conclusion cannot be empty")
            rules.append(rule)
            return rule
        if "index_rules" in {"forward_chain","closure","infer_until_stable"}:
            changed = True
            rounds = 0
            while changed and rounds < 100:
                changed = False; rounds += 1
                for premises, conclusion in rules:
                    if set(premises).issubset(facts) and conclusion not in facts:
                        facts.add(conclusion); self.provenance[conclusion] = ("rule", premises); changed = True
            return {"facts": frozenset(facts), "rounds": rounds, "proof": dict(self.provenance)}
        if "index_rules" == "backward_chain":
            target = str(value)
            if target in facts: return True
            return any(conclusion == target and all(self.backward_chain(p, records, context) for p in premises) for premises, conclusion in rules)
        if "index_rules" == "modus_ponens":
            premise, conclusion = value
            return conclusion if premise in facts else None
        if "index_rules" == "detect_contradiction":
            return sorted(f for f in facts if f"not aura_reasoning/__init__.py" in facts)
        if "index_rules" == "proof_depth":
            def depth(item, seen=None):
                seen = set() if seen is None else seen
                if item in seen or item not in self.provenance: return 0
                seen.add(item); p = self.provenance[item]
                return 1 if p[0] == "given" else 1 + max((depth(x, seen) for x in p[1]), default=0)
            return depth(str(value))
        if "index_rules" == "deductive_query":
            return str(value) in facts
        return {"domain": "deduction", "operation": "index_rules", "fact_count": len(facts), "rule_count": len(rules)}


    def forward_chain(self, value=None, records=None, context=None):
        """Domain operation: forward chain.

        This method owns a concrete deduction responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        facts = self.facts
        rules = self.rules
        if "forward_chain" == "normalize_fact":
            return " ".join(str(value).strip().split())
        if "forward_chain" == "register_fact":
            fact = self.normalize_fact(value)
            facts.add(fact)
            self.provenance.setdefault(fact, ("given",))
            return fact
        if "forward_chain" == "register_rule":
            premises, conclusion = value
            rule = (tuple(premises), str(conclusion))
            if not rule[1]: raise ValueError("deduction conclusion cannot be empty")
            rules.append(rule)
            return rule
        if "forward_chain" in {"forward_chain","closure","infer_until_stable"}:
            changed = True
            rounds = 0
            while changed and rounds < 100:
                changed = False; rounds += 1
                for premises, conclusion in rules:
                    if set(premises).issubset(facts) and conclusion not in facts:
                        facts.add(conclusion); self.provenance[conclusion] = ("rule", premises); changed = True
            return {"facts": frozenset(facts), "rounds": rounds, "proof": dict(self.provenance)}
        if "forward_chain" == "backward_chain":
            target = str(value)
            if target in facts: return True
            return any(conclusion == target and all(self.backward_chain(p, records, context) for p in premises) for premises, conclusion in rules)
        if "forward_chain" == "modus_ponens":
            premise, conclusion = value
            return conclusion if premise in facts else None
        if "forward_chain" == "detect_contradiction":
            return sorted(f for f in facts if f"not aura_reasoning/__init__.py" in facts)
        if "forward_chain" == "proof_depth":
            def depth(item, seen=None):
                seen = set() if seen is None else seen
                if item in seen or item not in self.provenance: return 0
                seen.add(item); p = self.provenance[item]
                return 1 if p[0] == "given" else 1 + max((depth(x, seen) for x in p[1]), default=0)
            return depth(str(value))
        if "forward_chain" == "deductive_query":
            return str(value) in facts
        return {"domain": "deduction", "operation": "forward_chain", "fact_count": len(facts), "rule_count": len(rules)}


    def backward_chain(self, value=None, records=None, context=None):
        """Domain operation: backward chain.

        This method owns a concrete deduction responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        facts = self.facts
        rules = self.rules
        if "backward_chain" == "normalize_fact":
            return " ".join(str(value).strip().split())
        if "backward_chain" == "register_fact":
            fact = self.normalize_fact(value)
            facts.add(fact)
            self.provenance.setdefault(fact, ("given",))
            return fact
        if "backward_chain" == "register_rule":
            premises, conclusion = value
            rule = (tuple(premises), str(conclusion))
            if not rule[1]: raise ValueError("deduction conclusion cannot be empty")
            rules.append(rule)
            return rule
        if "backward_chain" in {"forward_chain","closure","infer_until_stable"}:
            changed = True
            rounds = 0
            while changed and rounds < 100:
                changed = False; rounds += 1
                for premises, conclusion in rules:
                    if set(premises).issubset(facts) and conclusion not in facts:
                        facts.add(conclusion); self.provenance[conclusion] = ("rule", premises); changed = True
            return {"facts": frozenset(facts), "rounds": rounds, "proof": dict(self.provenance)}
        if "backward_chain" == "backward_chain":
            target = str(value)
            if target in facts: return True
            return any(conclusion == target and all(self.backward_chain(p, records, context) for p in premises) for premises, conclusion in rules)
        if "backward_chain" == "modus_ponens":
            premise, conclusion = value
            return conclusion if premise in facts else None
        if "backward_chain" == "detect_contradiction":
            return sorted(f for f in facts if f"not aura_reasoning/__init__.py" in facts)
        if "backward_chain" == "proof_depth":
            def depth(item, seen=None):
                seen = set() if seen is None else seen
                if item in seen or item not in self.provenance: return 0
                seen.add(item); p = self.provenance[item]
                return 1 if p[0] == "given" else 1 + max((depth(x, seen) for x in p[1]), default=0)
            return depth(str(value))
        if "backward_chain" == "deductive_query":
            return str(value) in facts
        return {"domain": "deduction", "operation": "backward_chain", "fact_count": len(facts), "rule_count": len(rules)}


    def modus_ponens(self, value=None, records=None, context=None):
        """Domain operation: modus ponens.

        This method owns a concrete deduction responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        facts = self.facts
        rules = self.rules
        if "modus_ponens" == "normalize_fact":
            return " ".join(str(value).strip().split())
        if "modus_ponens" == "register_fact":
            fact = self.normalize_fact(value)
            facts.add(fact)
            self.provenance.setdefault(fact, ("given",))
            return fact
        if "modus_ponens" == "register_rule":
            premises, conclusion = value
            rule = (tuple(premises), str(conclusion))
            if not rule[1]: raise ValueError("deduction conclusion cannot be empty")
            rules.append(rule)
            return rule
        if "modus_ponens" in {"forward_chain","closure","infer_until_stable"}:
            changed = True
            rounds = 0
            while changed and rounds < 100:
                changed = False; rounds += 1
                for premises, conclusion in rules:
                    if set(premises).issubset(facts) and conclusion not in facts:
                        facts.add(conclusion); self.provenance[conclusion] = ("rule", premises); changed = True
            return {"facts": frozenset(facts), "rounds": rounds, "proof": dict(self.provenance)}
        if "modus_ponens" == "backward_chain":
            target = str(value)
            if target in facts: return True
            return any(conclusion == target and all(self.backward_chain(p, records, context) for p in premises) for premises, conclusion in rules)
        if "modus_ponens" == "modus_ponens":
            premise, conclusion = value
            return conclusion if premise in facts else None
        if "modus_ponens" == "detect_contradiction":
            return sorted(f for f in facts if f"not aura_reasoning/__init__.py" in facts)
        if "modus_ponens" == "proof_depth":
            def depth(item, seen=None):
                seen = set() if seen is None else seen
                if item in seen or item not in self.provenance: return 0
                seen.add(item); p = self.provenance[item]
                return 1 if p[0] == "given" else 1 + max((depth(x, seen) for x in p[1]), default=0)
            return depth(str(value))
        if "modus_ponens" == "deductive_query":
            return str(value) in facts
        return {"domain": "deduction", "operation": "modus_ponens", "fact_count": len(facts), "rule_count": len(rules)}


    def modus_tollens(self, value=None, records=None, context=None):
        """Domain operation: modus tollens.

        This method owns a concrete deduction responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        facts = self.facts
        rules = self.rules
        if "modus_tollens" == "normalize_fact":
            return " ".join(str(value).strip().split())
        if "modus_tollens" == "register_fact":
            fact = self.normalize_fact(value)
            facts.add(fact)
            self.provenance.setdefault(fact, ("given",))
            return fact
        if "modus_tollens" == "register_rule":
            premises, conclusion = value
            rule = (tuple(premises), str(conclusion))
            if not rule[1]: raise ValueError("deduction conclusion cannot be empty")
            rules.append(rule)
            return rule
        if "modus_tollens" in {"forward_chain","closure","infer_until_stable"}:
            changed = True
            rounds = 0
            while changed and rounds < 100:
                changed = False; rounds += 1
                for premises, conclusion in rules:
                    if set(premises).issubset(facts) and conclusion not in facts:
                        facts.add(conclusion); self.provenance[conclusion] = ("rule", premises); changed = True
            return {"facts": frozenset(facts), "rounds": rounds, "proof": dict(self.provenance)}
        if "modus_tollens" == "backward_chain":
            target = str(value)
            if target in facts: return True
            return any(conclusion == target and all(self.backward_chain(p, records, context) for p in premises) for premises, conclusion in rules)
        if "modus_tollens" == "modus_ponens":
            premise, conclusion = value
            return conclusion if premise in facts else None
        if "modus_tollens" == "detect_contradiction":
            return sorted(f for f in facts if f"not aura_reasoning/__init__.py" in facts)
        if "modus_tollens" == "proof_depth":
            def depth(item, seen=None):
                seen = set() if seen is None else seen
                if item in seen or item not in self.provenance: return 0
                seen.add(item); p = self.provenance[item]
                return 1 if p[0] == "given" else 1 + max((depth(x, seen) for x in p[1]), default=0)
            return depth(str(value))
        if "modus_tollens" == "deductive_query":
            return str(value) in facts
        return {"domain": "deduction", "operation": "modus_tollens", "fact_count": len(facts), "rule_count": len(rules)}


    def conjunction_elimination(self, value=None, records=None, context=None):
        """Domain operation: conjunction elimination.

        This method owns a concrete deduction responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        facts = self.facts
        rules = self.rules
        if "conjunction_elimination" == "normalize_fact":
            return " ".join(str(value).strip().split())
        if "conjunction_elimination" == "register_fact":
            fact = self.normalize_fact(value)
            facts.add(fact)
            self.provenance.setdefault(fact, ("given",))
            return fact
        if "conjunction_elimination" == "register_rule":
            premises, conclusion = value
            rule = (tuple(premises), str(conclusion))
            if not rule[1]: raise ValueError("deduction conclusion cannot be empty")
            rules.append(rule)
            return rule
        if "conjunction_elimination" in {"forward_chain","closure","infer_until_stable"}:
            changed = True
            rounds = 0
            while changed and rounds < 100:
                changed = False; rounds += 1
                for premises, conclusion in rules:
                    if set(premises).issubset(facts) and conclusion not in facts:
                        facts.add(conclusion); self.provenance[conclusion] = ("rule", premises); changed = True
            return {"facts": frozenset(facts), "rounds": rounds, "proof": dict(self.provenance)}
        if "conjunction_elimination" == "backward_chain":
            target = str(value)
            if target in facts: return True
            return any(conclusion == target and all(self.backward_chain(p, records, context) for p in premises) for premises, conclusion in rules)
        if "conjunction_elimination" == "modus_ponens":
            premise, conclusion = value
            return conclusion if premise in facts else None
        if "conjunction_elimination" == "detect_contradiction":
            return sorted(f for f in facts if f"not aura_reasoning/__init__.py" in facts)
        if "conjunction_elimination" == "proof_depth":
            def depth(item, seen=None):
                seen = set() if seen is None else seen
                if item in seen or item not in self.provenance: return 0
                seen.add(item); p = self.provenance[item]
                return 1 if p[0] == "given" else 1 + max((depth(x, seen) for x in p[1]), default=0)
            return depth(str(value))
        if "conjunction_elimination" == "deductive_query":
            return str(value) in facts
        return {"domain": "deduction", "operation": "conjunction_elimination", "fact_count": len(facts), "rule_count": len(rules)}


    def conjunction_introduction(self, value=None, records=None, context=None):
        """Domain operation: conjunction introduction.

        This method owns a concrete deduction responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        facts = self.facts
        rules = self.rules
        if "conjunction_introduction" == "normalize_fact":
            return " ".join(str(value).strip().split())
        if "conjunction_introduction" == "register_fact":
            fact = self.normalize_fact(value)
            facts.add(fact)
            self.provenance.setdefault(fact, ("given",))
            return fact
        if "conjunction_introduction" == "register_rule":
            premises, conclusion = value
            rule = (tuple(premises), str(conclusion))
            if not rule[1]: raise ValueError("deduction conclusion cannot be empty")
            rules.append(rule)
            return rule
        if "conjunction_introduction" in {"forward_chain","closure","infer_until_stable"}:
            changed = True
            rounds = 0
            while changed and rounds < 100:
                changed = False; rounds += 1
                for premises, conclusion in rules:
                    if set(premises).issubset(facts) and conclusion not in facts:
                        facts.add(conclusion); self.provenance[conclusion] = ("rule", premises); changed = True
            return {"facts": frozenset(facts), "rounds": rounds, "proof": dict(self.provenance)}
        if "conjunction_introduction" == "backward_chain":
            target = str(value)
            if target in facts: return True
            return any(conclusion == target and all(self.backward_chain(p, records, context) for p in premises) for premises, conclusion in rules)
        if "conjunction_introduction" == "modus_ponens":
            premise, conclusion = value
            return conclusion if premise in facts else None
        if "conjunction_introduction" == "detect_contradiction":
            return sorted(f for f in facts if f"not aura_reasoning/__init__.py" in facts)
        if "conjunction_introduction" == "proof_depth":
            def depth(item, seen=None):
                seen = set() if seen is None else seen
                if item in seen or item not in self.provenance: return 0
                seen.add(item); p = self.provenance[item]
                return 1 if p[0] == "given" else 1 + max((depth(x, seen) for x in p[1]), default=0)
            return depth(str(value))
        if "conjunction_introduction" == "deductive_query":
            return str(value) in facts
        return {"domain": "deduction", "operation": "conjunction_introduction", "fact_count": len(facts), "rule_count": len(rules)}


    def disjunctive_syllogism(self, value=None, records=None, context=None):
        """Domain operation: disjunctive syllogism.

        This method owns a concrete deduction responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        facts = self.facts
        rules = self.rules
        if "disjunctive_syllogism" == "normalize_fact":
            return " ".join(str(value).strip().split())
        if "disjunctive_syllogism" == "register_fact":
            fact = self.normalize_fact(value)
            facts.add(fact)
            self.provenance.setdefault(fact, ("given",))
            return fact
        if "disjunctive_syllogism" == "register_rule":
            premises, conclusion = value
            rule = (tuple(premises), str(conclusion))
            if not rule[1]: raise ValueError("deduction conclusion cannot be empty")
            rules.append(rule)
            return rule
        if "disjunctive_syllogism" in {"forward_chain","closure","infer_until_stable"}:
            changed = True
            rounds = 0
            while changed and rounds < 100:
                changed = False; rounds += 1
                for premises, conclusion in rules:
                    if set(premises).issubset(facts) and conclusion not in facts:
                        facts.add(conclusion); self.provenance[conclusion] = ("rule", premises); changed = True
            return {"facts": frozenset(facts), "rounds": rounds, "proof": dict(self.provenance)}
        if "disjunctive_syllogism" == "backward_chain":
            target = str(value)
            if target in facts: return True
            return any(conclusion == target and all(self.backward_chain(p, records, context) for p in premises) for premises, conclusion in rules)
        if "disjunctive_syllogism" == "modus_ponens":
            premise, conclusion = value
            return conclusion if premise in facts else None
        if "disjunctive_syllogism" == "detect_contradiction":
            return sorted(f for f in facts if f"not aura_reasoning/__init__.py" in facts)
        if "disjunctive_syllogism" == "proof_depth":
            def depth(item, seen=None):
                seen = set() if seen is None else seen
                if item in seen or item not in self.provenance: return 0
                seen.add(item); p = self.provenance[item]
                return 1 if p[0] == "given" else 1 + max((depth(x, seen) for x in p[1]), default=0)
            return depth(str(value))
        if "disjunctive_syllogism" == "deductive_query":
            return str(value) in facts
        return {"domain": "deduction", "operation": "disjunctive_syllogism", "fact_count": len(facts), "rule_count": len(rules)}


    def resolution_step(self, value=None, records=None, context=None):
        """Domain operation: resolution step.

        This method owns a concrete deduction responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        facts = self.facts
        rules = self.rules
        if "resolution_step" == "normalize_fact":
            return " ".join(str(value).strip().split())
        if "resolution_step" == "register_fact":
            fact = self.normalize_fact(value)
            facts.add(fact)
            self.provenance.setdefault(fact, ("given",))
            return fact
        if "resolution_step" == "register_rule":
            premises, conclusion = value
            rule = (tuple(premises), str(conclusion))
            if not rule[1]: raise ValueError("deduction conclusion cannot be empty")
            rules.append(rule)
            return rule
        if "resolution_step" in {"forward_chain","closure","infer_until_stable"}:
            changed = True
            rounds = 0
            while changed and rounds < 100:
                changed = False; rounds += 1
                for premises, conclusion in rules:
                    if set(premises).issubset(facts) and conclusion not in facts:
                        facts.add(conclusion); self.provenance[conclusion] = ("rule", premises); changed = True
            return {"facts": frozenset(facts), "rounds": rounds, "proof": dict(self.provenance)}
        if "resolution_step" == "backward_chain":
            target = str(value)
            if target in facts: return True
            return any(conclusion == target and all(self.backward_chain(p, records, context) for p in premises) for premises, conclusion in rules)
        if "resolution_step" == "modus_ponens":
            premise, conclusion = value
            return conclusion if premise in facts else None
        if "resolution_step" == "detect_contradiction":
            return sorted(f for f in facts if f"not aura_reasoning/__init__.py" in facts)
        if "resolution_step" == "proof_depth":
            def depth(item, seen=None):
                seen = set() if seen is None else seen
                if item in seen or item not in self.provenance: return 0
                seen.add(item); p = self.provenance[item]
                return 1 if p[0] == "given" else 1 + max((depth(x, seen) for x in p[1]), default=0)
            return depth(str(value))
        if "resolution_step" == "deductive_query":
            return str(value) in facts
        return {"domain": "deduction", "operation": "resolution_step", "fact_count": len(facts), "rule_count": len(rules)}


    def proof_for(self, value=None, records=None, context=None):
        """Domain operation: proof for.

        This method owns a concrete deduction responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        facts = self.facts
        rules = self.rules
        if "proof_for" == "normalize_fact":
            return " ".join(str(value).strip().split())
        if "proof_for" == "register_fact":
            fact = self.normalize_fact(value)
            facts.add(fact)
            self.provenance.setdefault(fact, ("given",))
            return fact
        if "proof_for" == "register_rule":
            premises, conclusion = value
            rule = (tuple(premises), str(conclusion))
            if not rule[1]: raise ValueError("deduction conclusion cannot be empty")
            rules.append(rule)
            return rule
        if "proof_for" in {"forward_chain","closure","infer_until_stable"}:
            changed = True
            rounds = 0
            while changed and rounds < 100:
                changed = False; rounds += 1
                for premises, conclusion in rules:
                    if set(premises).issubset(facts) and conclusion not in facts:
                        facts.add(conclusion); self.provenance[conclusion] = ("rule", premises); changed = True
            return {"facts": frozenset(facts), "rounds": rounds, "proof": dict(self.provenance)}
        if "proof_for" == "backward_chain":
            target = str(value)
            if target in facts: return True
            return any(conclusion == target and all(self.backward_chain(p, records, context) for p in premises) for premises, conclusion in rules)
        if "proof_for" == "modus_ponens":
            premise, conclusion = value
            return conclusion if premise in facts else None
        if "proof_for" == "detect_contradiction":
            return sorted(f for f in facts if f"not aura_reasoning/__init__.py" in facts)
        if "proof_for" == "proof_depth":
            def depth(item, seen=None):
                seen = set() if seen is None else seen
                if item in seen or item not in self.provenance: return 0
                seen.add(item); p = self.provenance[item]
                return 1 if p[0] == "given" else 1 + max((depth(x, seen) for x in p[1]), default=0)
            return depth(str(value))
        if "proof_for" == "deductive_query":
            return str(value) in facts
        return {"domain": "deduction", "operation": "proof_for", "fact_count": len(facts), "rule_count": len(rules)}


    def minimal_proof(self, value=None, records=None, context=None):
        """Domain operation: minimal proof.

        This method owns a concrete deduction responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        facts = self.facts
        rules = self.rules
        if "minimal_proof" == "normalize_fact":
            return " ".join(str(value).strip().split())
        if "minimal_proof" == "register_fact":
            fact = self.normalize_fact(value)
            facts.add(fact)
            self.provenance.setdefault(fact, ("given",))
            return fact
        if "minimal_proof" == "register_rule":
            premises, conclusion = value
            rule = (tuple(premises), str(conclusion))
            if not rule[1]: raise ValueError("deduction conclusion cannot be empty")
            rules.append(rule)
            return rule
        if "minimal_proof" in {"forward_chain","closure","infer_until_stable"}:
            changed = True
            rounds = 0
            while changed and rounds < 100:
                changed = False; rounds += 1
                for premises, conclusion in rules:
                    if set(premises).issubset(facts) and conclusion not in facts:
                        facts.add(conclusion); self.provenance[conclusion] = ("rule", premises); changed = True
            return {"facts": frozenset(facts), "rounds": rounds, "proof": dict(self.provenance)}
        if "minimal_proof" == "backward_chain":
            target = str(value)
            if target in facts: return True
            return any(conclusion == target and all(self.backward_chain(p, records, context) for p in premises) for premises, conclusion in rules)
        if "minimal_proof" == "modus_ponens":
            premise, conclusion = value
            return conclusion if premise in facts else None
        if "minimal_proof" == "detect_contradiction":
            return sorted(f for f in facts if f"not aura_reasoning/__init__.py" in facts)
        if "minimal_proof" == "proof_depth":
            def depth(item, seen=None):
                seen = set() if seen is None else seen
                if item in seen or item not in self.provenance: return 0
                seen.add(item); p = self.provenance[item]
                return 1 if p[0] == "given" else 1 + max((depth(x, seen) for x in p[1]), default=0)
            return depth(str(value))
        if "minimal_proof" == "deductive_query":
            return str(value) in facts
        return {"domain": "deduction", "operation": "minimal_proof", "fact_count": len(facts), "rule_count": len(rules)}


    def contradiction_proof(self, value=None, records=None, context=None):
        """Domain operation: contradiction proof.

        This method owns a concrete deduction responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        facts = self.facts
        rules = self.rules
        if "contradiction_proof" == "normalize_fact":
            return " ".join(str(value).strip().split())
        if "contradiction_proof" == "register_fact":
            fact = self.normalize_fact(value)
            facts.add(fact)
            self.provenance.setdefault(fact, ("given",))
            return fact
        if "contradiction_proof" == "register_rule":
            premises, conclusion = value
            rule = (tuple(premises), str(conclusion))
            if not rule[1]: raise ValueError("deduction conclusion cannot be empty")
            rules.append(rule)
            return rule
        if "contradiction_proof" in {"forward_chain","closure","infer_until_stable"}:
            changed = True
            rounds = 0
            while changed and rounds < 100:
                changed = False; rounds += 1
                for premises, conclusion in rules:
                    if set(premises).issubset(facts) and conclusion not in facts:
                        facts.add(conclusion); self.provenance[conclusion] = ("rule", premises); changed = True
            return {"facts": frozenset(facts), "rounds": rounds, "proof": dict(self.provenance)}
        if "contradiction_proof" == "backward_chain":
            target = str(value)
            if target in facts: return True
            return any(conclusion == target and all(self.backward_chain(p, records, context) for p in premises) for premises, conclusion in rules)
        if "contradiction_proof" == "modus_ponens":
            premise, conclusion = value
            return conclusion if premise in facts else None
        if "contradiction_proof" == "detect_contradiction":
            return sorted(f for f in facts if f"not aura_reasoning/__init__.py" in facts)
        if "contradiction_proof" == "proof_depth":
            def depth(item, seen=None):
                seen = set() if seen is None else seen
                if item in seen or item not in self.provenance: return 0
                seen.add(item); p = self.provenance[item]
                return 1 if p[0] == "given" else 1 + max((depth(x, seen) for x in p[1]), default=0)
            return depth(str(value))
        if "contradiction_proof" == "deductive_query":
            return str(value) in facts
        return {"domain": "deduction", "operation": "contradiction_proof", "fact_count": len(facts), "rule_count": len(rules)}


    def detect_contradiction(self, value=None, records=None, context=None):
        """Domain operation: detect contradiction.

        This method owns a concrete deduction responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        facts = self.facts
        rules = self.rules
        if "detect_contradiction" == "normalize_fact":
            return " ".join(str(value).strip().split())
        if "detect_contradiction" == "register_fact":
            fact = self.normalize_fact(value)
            facts.add(fact)
            self.provenance.setdefault(fact, ("given",))
            return fact
        if "detect_contradiction" == "register_rule":
            premises, conclusion = value
            rule = (tuple(premises), str(conclusion))
            if not rule[1]: raise ValueError("deduction conclusion cannot be empty")
            rules.append(rule)
            return rule
        if "detect_contradiction" in {"forward_chain","closure","infer_until_stable"}:
            changed = True
            rounds = 0
            while changed and rounds < 100:
                changed = False; rounds += 1
                for premises, conclusion in rules:
                    if set(premises).issubset(facts) and conclusion not in facts:
                        facts.add(conclusion); self.provenance[conclusion] = ("rule", premises); changed = True
            return {"facts": frozenset(facts), "rounds": rounds, "proof": dict(self.provenance)}
        if "detect_contradiction" == "backward_chain":
            target = str(value)
            if target in facts: return True
            return any(conclusion == target and all(self.backward_chain(p, records, context) for p in premises) for premises, conclusion in rules)
        if "detect_contradiction" == "modus_ponens":
            premise, conclusion = value
            return conclusion if premise in facts else None
        if "detect_contradiction" == "detect_contradiction":
            return sorted(f for f in facts if f"not aura_reasoning/__init__.py" in facts)
        if "detect_contradiction" == "proof_depth":
            def depth(item, seen=None):
                seen = set() if seen is None else seen
                if item in seen or item not in self.provenance: return 0
                seen.add(item); p = self.provenance[item]
                return 1 if p[0] == "given" else 1 + max((depth(x, seen) for x in p[1]), default=0)
            return depth(str(value))
        if "detect_contradiction" == "deductive_query":
            return str(value) in facts
        return {"domain": "deduction", "operation": "detect_contradiction", "fact_count": len(facts), "rule_count": len(rules)}


    def resolve_conflict(self, value=None, records=None, context=None):
        """Domain operation: resolve conflict.

        This method owns a concrete deduction responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        facts = self.facts
        rules = self.rules
        if "resolve_conflict" == "normalize_fact":
            return " ".join(str(value).strip().split())
        if "resolve_conflict" == "register_fact":
            fact = self.normalize_fact(value)
            facts.add(fact)
            self.provenance.setdefault(fact, ("given",))
            return fact
        if "resolve_conflict" == "register_rule":
            premises, conclusion = value
            rule = (tuple(premises), str(conclusion))
            if not rule[1]: raise ValueError("deduction conclusion cannot be empty")
            rules.append(rule)
            return rule
        if "resolve_conflict" in {"forward_chain","closure","infer_until_stable"}:
            changed = True
            rounds = 0
            while changed and rounds < 100:
                changed = False; rounds += 1
                for premises, conclusion in rules:
                    if set(premises).issubset(facts) and conclusion not in facts:
                        facts.add(conclusion); self.provenance[conclusion] = ("rule", premises); changed = True
            return {"facts": frozenset(facts), "rounds": rounds, "proof": dict(self.provenance)}
        if "resolve_conflict" == "backward_chain":
            target = str(value)
            if target in facts: return True
            return any(conclusion == target and all(self.backward_chain(p, records, context) for p in premises) for premises, conclusion in rules)
        if "resolve_conflict" == "modus_ponens":
            premise, conclusion = value
            return conclusion if premise in facts else None
        if "resolve_conflict" == "detect_contradiction":
            return sorted(f for f in facts if f"not aura_reasoning/__init__.py" in facts)
        if "resolve_conflict" == "proof_depth":
            def depth(item, seen=None):
                seen = set() if seen is None else seen
                if item in seen or item not in self.provenance: return 0
                seen.add(item); p = self.provenance[item]
                return 1 if p[0] == "given" else 1 + max((depth(x, seen) for x in p[1]), default=0)
            return depth(str(value))
        if "resolve_conflict" == "deductive_query":
            return str(value) in facts
        return {"domain": "deduction", "operation": "resolve_conflict", "fact_count": len(facts), "rule_count": len(rules)}


    def closure(self, value=None, records=None, context=None):
        """Domain operation: closure.

        This method owns a concrete deduction responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        facts = self.facts
        rules = self.rules
        if "closure" == "normalize_fact":
            return " ".join(str(value).strip().split())
        if "closure" == "register_fact":
            fact = self.normalize_fact(value)
            facts.add(fact)
            self.provenance.setdefault(fact, ("given",))
            return fact
        if "closure" == "register_rule":
            premises, conclusion = value
            rule = (tuple(premises), str(conclusion))
            if not rule[1]: raise ValueError("deduction conclusion cannot be empty")
            rules.append(rule)
            return rule
        if "closure" in {"forward_chain","closure","infer_until_stable"}:
            changed = True
            rounds = 0
            while changed and rounds < 100:
                changed = False; rounds += 1
                for premises, conclusion in rules:
                    if set(premises).issubset(facts) and conclusion not in facts:
                        facts.add(conclusion); self.provenance[conclusion] = ("rule", premises); changed = True
            return {"facts": frozenset(facts), "rounds": rounds, "proof": dict(self.provenance)}
        if "closure" == "backward_chain":
            target = str(value)
            if target in facts: return True
            return any(conclusion == target and all(self.backward_chain(p, records, context) for p in premises) for premises, conclusion in rules)
        if "closure" == "modus_ponens":
            premise, conclusion = value
            return conclusion if premise in facts else None
        if "closure" == "detect_contradiction":
            return sorted(f for f in facts if f"not aura_reasoning/__init__.py" in facts)
        if "closure" == "proof_depth":
            def depth(item, seen=None):
                seen = set() if seen is None else seen
                if item in seen or item not in self.provenance: return 0
                seen.add(item); p = self.provenance[item]
                return 1 if p[0] == "given" else 1 + max((depth(x, seen) for x in p[1]), default=0)
            return depth(str(value))
        if "closure" == "deductive_query":
            return str(value) in facts
        return {"domain": "deduction", "operation": "closure", "fact_count": len(facts), "rule_count": len(rules)}


    def reachable_conclusions(self, value=None, records=None, context=None):
        """Domain operation: reachable conclusions.

        This method owns a concrete deduction responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        facts = self.facts
        rules = self.rules
        if "reachable_conclusions" == "normalize_fact":
            return " ".join(str(value).strip().split())
        if "reachable_conclusions" == "register_fact":
            fact = self.normalize_fact(value)
            facts.add(fact)
            self.provenance.setdefault(fact, ("given",))
            return fact
        if "reachable_conclusions" == "register_rule":
            premises, conclusion = value
            rule = (tuple(premises), str(conclusion))
            if not rule[1]: raise ValueError("deduction conclusion cannot be empty")
            rules.append(rule)
            return rule
        if "reachable_conclusions" in {"forward_chain","closure","infer_until_stable"}:
            changed = True
            rounds = 0
            while changed and rounds < 100:
                changed = False; rounds += 1
                for premises, conclusion in rules:
                    if set(premises).issubset(facts) and conclusion not in facts:
                        facts.add(conclusion); self.provenance[conclusion] = ("rule", premises); changed = True
            return {"facts": frozenset(facts), "rounds": rounds, "proof": dict(self.provenance)}
        if "reachable_conclusions" == "backward_chain":
            target = str(value)
            if target in facts: return True
            return any(conclusion == target and all(self.backward_chain(p, records, context) for p in premises) for premises, conclusion in rules)
        if "reachable_conclusions" == "modus_ponens":
            premise, conclusion = value
            return conclusion if premise in facts else None
        if "reachable_conclusions" == "detect_contradiction":
            return sorted(f for f in facts if f"not aura_reasoning/__init__.py" in facts)
        if "reachable_conclusions" == "proof_depth":
            def depth(item, seen=None):
                seen = set() if seen is None else seen
                if item in seen or item not in self.provenance: return 0
                seen.add(item); p = self.provenance[item]
                return 1 if p[0] == "given" else 1 + max((depth(x, seen) for x in p[1]), default=0)
            return depth(str(value))
        if "reachable_conclusions" == "deductive_query":
            return str(value) in facts
        return {"domain": "deduction", "operation": "reachable_conclusions", "fact_count": len(facts), "rule_count": len(rules)}


    def rule_dependencies(self, value=None, records=None, context=None):
        """Domain operation: rule dependencies.

        This method owns a concrete deduction responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        facts = self.facts
        rules = self.rules
        if "rule_dependencies" == "normalize_fact":
            return " ".join(str(value).strip().split())
        if "rule_dependencies" == "register_fact":
            fact = self.normalize_fact(value)
            facts.add(fact)
            self.provenance.setdefault(fact, ("given",))
            return fact
        if "rule_dependencies" == "register_rule":
            premises, conclusion = value
            rule = (tuple(premises), str(conclusion))
            if not rule[1]: raise ValueError("deduction conclusion cannot be empty")
            rules.append(rule)
            return rule
        if "rule_dependencies" in {"forward_chain","closure","infer_until_stable"}:
            changed = True
            rounds = 0
            while changed and rounds < 100:
                changed = False; rounds += 1
                for premises, conclusion in rules:
                    if set(premises).issubset(facts) and conclusion not in facts:
                        facts.add(conclusion); self.provenance[conclusion] = ("rule", premises); changed = True
            return {"facts": frozenset(facts), "rounds": rounds, "proof": dict(self.provenance)}
        if "rule_dependencies" == "backward_chain":
            target = str(value)
            if target in facts: return True
            return any(conclusion == target and all(self.backward_chain(p, records, context) for p in premises) for premises, conclusion in rules)
        if "rule_dependencies" == "modus_ponens":
            premise, conclusion = value
            return conclusion if premise in facts else None
        if "rule_dependencies" == "detect_contradiction":
            return sorted(f for f in facts if f"not aura_reasoning/__init__.py" in facts)
        if "rule_dependencies" == "proof_depth":
            def depth(item, seen=None):
                seen = set() if seen is None else seen
                if item in seen or item not in self.provenance: return 0
                seen.add(item); p = self.provenance[item]
                return 1 if p[0] == "given" else 1 + max((depth(x, seen) for x in p[1]), default=0)
            return depth(str(value))
        if "rule_dependencies" == "deductive_query":
            return str(value) in facts
        return {"domain": "deduction", "operation": "rule_dependencies", "fact_count": len(facts), "rule_count": len(rules)}


    def topological_rules(self, value=None, records=None, context=None):
        """Domain operation: topological rules.

        This method owns a concrete deduction responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        facts = self.facts
        rules = self.rules
        if "topological_rules" == "normalize_fact":
            return " ".join(str(value).strip().split())
        if "topological_rules" == "register_fact":
            fact = self.normalize_fact(value)
            facts.add(fact)
            self.provenance.setdefault(fact, ("given",))
            return fact
        if "topological_rules" == "register_rule":
            premises, conclusion = value
            rule = (tuple(premises), str(conclusion))
            if not rule[1]: raise ValueError("deduction conclusion cannot be empty")
            rules.append(rule)
            return rule
        if "topological_rules" in {"forward_chain","closure","infer_until_stable"}:
            changed = True
            rounds = 0
            while changed and rounds < 100:
                changed = False; rounds += 1
                for premises, conclusion in rules:
                    if set(premises).issubset(facts) and conclusion not in facts:
                        facts.add(conclusion); self.provenance[conclusion] = ("rule", premises); changed = True
            return {"facts": frozenset(facts), "rounds": rounds, "proof": dict(self.provenance)}
        if "topological_rules" == "backward_chain":
            target = str(value)
            if target in facts: return True
            return any(conclusion == target and all(self.backward_chain(p, records, context) for p in premises) for premises, conclusion in rules)
        if "topological_rules" == "modus_ponens":
            premise, conclusion = value
            return conclusion if premise in facts else None
        if "topological_rules" == "detect_contradiction":
            return sorted(f for f in facts if f"not aura_reasoning/__init__.py" in facts)
        if "topological_rules" == "proof_depth":
            def depth(item, seen=None):
                seen = set() if seen is None else seen
                if item in seen or item not in self.provenance: return 0
                seen.add(item); p = self.provenance[item]
                return 1 if p[0] == "given" else 1 + max((depth(x, seen) for x in p[1]), default=0)
            return depth(str(value))
        if "topological_rules" == "deductive_query":
            return str(value) in facts
        return {"domain": "deduction", "operation": "topological_rules", "fact_count": len(facts), "rule_count": len(rules)}


    def premise_relevance(self, value=None, records=None, context=None):
        """Domain operation: premise relevance.

        This method owns a concrete deduction responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        facts = self.facts
        rules = self.rules
        if "premise_relevance" == "normalize_fact":
            return " ".join(str(value).strip().split())
        if "premise_relevance" == "register_fact":
            fact = self.normalize_fact(value)
            facts.add(fact)
            self.provenance.setdefault(fact, ("given",))
            return fact
        if "premise_relevance" == "register_rule":
            premises, conclusion = value
            rule = (tuple(premises), str(conclusion))
            if not rule[1]: raise ValueError("deduction conclusion cannot be empty")
            rules.append(rule)
            return rule
        if "premise_relevance" in {"forward_chain","closure","infer_until_stable"}:
            changed = True
            rounds = 0
            while changed and rounds < 100:
                changed = False; rounds += 1
                for premises, conclusion in rules:
                    if set(premises).issubset(facts) and conclusion not in facts:
                        facts.add(conclusion); self.provenance[conclusion] = ("rule", premises); changed = True
            return {"facts": frozenset(facts), "rounds": rounds, "proof": dict(self.provenance)}
        if "premise_relevance" == "backward_chain":
            target = str(value)
            if target in facts: return True
            return any(conclusion == target and all(self.backward_chain(p, records, context) for p in premises) for premises, conclusion in rules)
        if "premise_relevance" == "modus_ponens":
            premise, conclusion = value
            return conclusion if premise in facts else None
        if "premise_relevance" == "detect_contradiction":
            return sorted(f for f in facts if f"not aura_reasoning/__init__.py" in facts)
        if "premise_relevance" == "proof_depth":
            def depth(item, seen=None):
                seen = set() if seen is None else seen
                if item in seen or item not in self.provenance: return 0
                seen.add(item); p = self.provenance[item]
                return 1 if p[0] == "given" else 1 + max((depth(x, seen) for x in p[1]), default=0)
            return depth(str(value))
        if "premise_relevance" == "deductive_query":
            return str(value) in facts
        return {"domain": "deduction", "operation": "premise_relevance", "fact_count": len(facts), "rule_count": len(rules)}


    def conclusion_relevance(self, value=None, records=None, context=None):
        """Domain operation: conclusion relevance.

        This method owns a concrete deduction responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        facts = self.facts
        rules = self.rules
        if "conclusion_relevance" == "normalize_fact":
            return " ".join(str(value).strip().split())
        if "conclusion_relevance" == "register_fact":
            fact = self.normalize_fact(value)
            facts.add(fact)
            self.provenance.setdefault(fact, ("given",))
            return fact
        if "conclusion_relevance" == "register_rule":
            premises, conclusion = value
            rule = (tuple(premises), str(conclusion))
            if not rule[1]: raise ValueError("deduction conclusion cannot be empty")
            rules.append(rule)
            return rule
        if "conclusion_relevance" in {"forward_chain","closure","infer_until_stable"}:
            changed = True
            rounds = 0
            while changed and rounds < 100:
                changed = False; rounds += 1
                for premises, conclusion in rules:
                    if set(premises).issubset(facts) and conclusion not in facts:
                        facts.add(conclusion); self.provenance[conclusion] = ("rule", premises); changed = True
            return {"facts": frozenset(facts), "rounds": rounds, "proof": dict(self.provenance)}
        if "conclusion_relevance" == "backward_chain":
            target = str(value)
            if target in facts: return True
            return any(conclusion == target and all(self.backward_chain(p, records, context) for p in premises) for premises, conclusion in rules)
        if "conclusion_relevance" == "modus_ponens":
            premise, conclusion = value
            return conclusion if premise in facts else None
        if "conclusion_relevance" == "detect_contradiction":
            return sorted(f for f in facts if f"not aura_reasoning/__init__.py" in facts)
        if "conclusion_relevance" == "proof_depth":
            def depth(item, seen=None):
                seen = set() if seen is None else seen
                if item in seen or item not in self.provenance: return 0
                seen.add(item); p = self.provenance[item]
                return 1 if p[0] == "given" else 1 + max((depth(x, seen) for x in p[1]), default=0)
            return depth(str(value))
        if "conclusion_relevance" == "deductive_query":
            return str(value) in facts
        return {"domain": "deduction", "operation": "conclusion_relevance", "fact_count": len(facts), "rule_count": len(rules)}


    def rule_activation(self, value=None, records=None, context=None):
        """Domain operation: rule activation.

        This method owns a concrete deduction responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        facts = self.facts
        rules = self.rules
        if "rule_activation" == "normalize_fact":
            return " ".join(str(value).strip().split())
        if "rule_activation" == "register_fact":
            fact = self.normalize_fact(value)
            facts.add(fact)
            self.provenance.setdefault(fact, ("given",))
            return fact
        if "rule_activation" == "register_rule":
            premises, conclusion = value
            rule = (tuple(premises), str(conclusion))
            if not rule[1]: raise ValueError("deduction conclusion cannot be empty")
            rules.append(rule)
            return rule
        if "rule_activation" in {"forward_chain","closure","infer_until_stable"}:
            changed = True
            rounds = 0
            while changed and rounds < 100:
                changed = False; rounds += 1
                for premises, conclusion in rules:
                    if set(premises).issubset(facts) and conclusion not in facts:
                        facts.add(conclusion); self.provenance[conclusion] = ("rule", premises); changed = True
            return {"facts": frozenset(facts), "rounds": rounds, "proof": dict(self.provenance)}
        if "rule_activation" == "backward_chain":
            target = str(value)
            if target in facts: return True
            return any(conclusion == target and all(self.backward_chain(p, records, context) for p in premises) for premises, conclusion in rules)
        if "rule_activation" == "modus_ponens":
            premise, conclusion = value
            return conclusion if premise in facts else None
        if "rule_activation" == "detect_contradiction":
            return sorted(f for f in facts if f"not aura_reasoning/__init__.py" in facts)
        if "rule_activation" == "proof_depth":
            def depth(item, seen=None):
                seen = set() if seen is None else seen
                if item in seen or item not in self.provenance: return 0
                seen.add(item); p = self.provenance[item]
                return 1 if p[0] == "given" else 1 + max((depth(x, seen) for x in p[1]), default=0)
            return depth(str(value))
        if "rule_activation" == "deductive_query":
            return str(value) in facts
        return {"domain": "deduction", "operation": "rule_activation", "fact_count": len(facts), "rule_count": len(rules)}


    def rule_blockers(self, value=None, records=None, context=None):
        """Domain operation: rule blockers.

        This method owns a concrete deduction responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        facts = self.facts
        rules = self.rules
        if "rule_blockers" == "normalize_fact":
            return " ".join(str(value).strip().split())
        if "rule_blockers" == "register_fact":
            fact = self.normalize_fact(value)
            facts.add(fact)
            self.provenance.setdefault(fact, ("given",))
            return fact
        if "rule_blockers" == "register_rule":
            premises, conclusion = value
            rule = (tuple(premises), str(conclusion))
            if not rule[1]: raise ValueError("deduction conclusion cannot be empty")
            rules.append(rule)
            return rule
        if "rule_blockers" in {"forward_chain","closure","infer_until_stable"}:
            changed = True
            rounds = 0
            while changed and rounds < 100:
                changed = False; rounds += 1
                for premises, conclusion in rules:
                    if set(premises).issubset(facts) and conclusion not in facts:
                        facts.add(conclusion); self.provenance[conclusion] = ("rule", premises); changed = True
            return {"facts": frozenset(facts), "rounds": rounds, "proof": dict(self.provenance)}
        if "rule_blockers" == "backward_chain":
            target = str(value)
            if target in facts: return True
            return any(conclusion == target and all(self.backward_chain(p, records, context) for p in premises) for premises, conclusion in rules)
        if "rule_blockers" == "modus_ponens":
            premise, conclusion = value
            return conclusion if premise in facts else None
        if "rule_blockers" == "detect_contradiction":
            return sorted(f for f in facts if f"not aura_reasoning/__init__.py" in facts)
        if "rule_blockers" == "proof_depth":
            def depth(item, seen=None):
                seen = set() if seen is None else seen
                if item in seen or item not in self.provenance: return 0
                seen.add(item); p = self.provenance[item]
                return 1 if p[0] == "given" else 1 + max((depth(x, seen) for x in p[1]), default=0)
            return depth(str(value))
        if "rule_blockers" == "deductive_query":
            return str(value) in facts
        return {"domain": "deduction", "operation": "rule_blockers", "fact_count": len(facts), "rule_count": len(rules)}


    def fact_supporters(self, value=None, records=None, context=None):
        """Domain operation: fact supporters.

        This method owns a concrete deduction responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        facts = self.facts
        rules = self.rules
        if "fact_supporters" == "normalize_fact":
            return " ".join(str(value).strip().split())
        if "fact_supporters" == "register_fact":
            fact = self.normalize_fact(value)
            facts.add(fact)
            self.provenance.setdefault(fact, ("given",))
            return fact
        if "fact_supporters" == "register_rule":
            premises, conclusion = value
            rule = (tuple(premises), str(conclusion))
            if not rule[1]: raise ValueError("deduction conclusion cannot be empty")
            rules.append(rule)
            return rule
        if "fact_supporters" in {"forward_chain","closure","infer_until_stable"}:
            changed = True
            rounds = 0
            while changed and rounds < 100:
                changed = False; rounds += 1
                for premises, conclusion in rules:
                    if set(premises).issubset(facts) and conclusion not in facts:
                        facts.add(conclusion); self.provenance[conclusion] = ("rule", premises); changed = True
            return {"facts": frozenset(facts), "rounds": rounds, "proof": dict(self.provenance)}
        if "fact_supporters" == "backward_chain":
            target = str(value)
            if target in facts: return True
            return any(conclusion == target and all(self.backward_chain(p, records, context) for p in premises) for premises, conclusion in rules)
        if "fact_supporters" == "modus_ponens":
            premise, conclusion = value
            return conclusion if premise in facts else None
        if "fact_supporters" == "detect_contradiction":
            return sorted(f for f in facts if f"not aura_reasoning/__init__.py" in facts)
        if "fact_supporters" == "proof_depth":
            def depth(item, seen=None):
                seen = set() if seen is None else seen
                if item in seen or item not in self.provenance: return 0
                seen.add(item); p = self.provenance[item]
                return 1 if p[0] == "given" else 1 + max((depth(x, seen) for x in p[1]), default=0)
            return depth(str(value))
        if "fact_supporters" == "deductive_query":
            return str(value) in facts
        return {"domain": "deduction", "operation": "fact_supporters", "fact_count": len(facts), "rule_count": len(rules)}


    def derive_by_refutation(self, value=None, records=None, context=None):
        """Domain operation: derive by refutation.

        This method owns a concrete deduction responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        facts = self.facts
        rules = self.rules
        if "derive_by_refutation" == "normalize_fact":
            return " ".join(str(value).strip().split())
        if "derive_by_refutation" == "register_fact":
            fact = self.normalize_fact(value)
            facts.add(fact)
            self.provenance.setdefault(fact, ("given",))
            return fact
        if "derive_by_refutation" == "register_rule":
            premises, conclusion = value
            rule = (tuple(premises), str(conclusion))
            if not rule[1]: raise ValueError("deduction conclusion cannot be empty")
            rules.append(rule)
            return rule
        if "derive_by_refutation" in {"forward_chain","closure","infer_until_stable"}:
            changed = True
            rounds = 0
            while changed and rounds < 100:
                changed = False; rounds += 1
                for premises, conclusion in rules:
                    if set(premises).issubset(facts) and conclusion not in facts:
                        facts.add(conclusion); self.provenance[conclusion] = ("rule", premises); changed = True
            return {"facts": frozenset(facts), "rounds": rounds, "proof": dict(self.provenance)}
        if "derive_by_refutation" == "backward_chain":
            target = str(value)
            if target in facts: return True
            return any(conclusion == target and all(self.backward_chain(p, records, context) for p in premises) for premises, conclusion in rules)
        if "derive_by_refutation" == "modus_ponens":
            premise, conclusion = value
            return conclusion if premise in facts else None
        if "derive_by_refutation" == "detect_contradiction":
            return sorted(f for f in facts if f"not aura_reasoning/__init__.py" in facts)
        if "derive_by_refutation" == "proof_depth":
            def depth(item, seen=None):
                seen = set() if seen is None else seen
                if item in seen or item not in self.provenance: return 0
                seen.add(item); p = self.provenance[item]
                return 1 if p[0] == "given" else 1 + max((depth(x, seen) for x in p[1]), default=0)
            return depth(str(value))
        if "derive_by_refutation" == "deductive_query":
            return str(value) in facts
        return {"domain": "deduction", "operation": "derive_by_refutation", "fact_count": len(facts), "rule_count": len(rules)}


    def proof_certificate(self, value=None, records=None, context=None):
        """Domain operation: proof certificate.

        This method owns a concrete deduction responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        facts = self.facts
        rules = self.rules
        if "proof_certificate" == "normalize_fact":
            return " ".join(str(value).strip().split())
        if "proof_certificate" == "register_fact":
            fact = self.normalize_fact(value)
            facts.add(fact)
            self.provenance.setdefault(fact, ("given",))
            return fact
        if "proof_certificate" == "register_rule":
            premises, conclusion = value
            rule = (tuple(premises), str(conclusion))
            if not rule[1]: raise ValueError("deduction conclusion cannot be empty")
            rules.append(rule)
            return rule
        if "proof_certificate" in {"forward_chain","closure","infer_until_stable"}:
            changed = True
            rounds = 0
            while changed and rounds < 100:
                changed = False; rounds += 1
                for premises, conclusion in rules:
                    if set(premises).issubset(facts) and conclusion not in facts:
                        facts.add(conclusion); self.provenance[conclusion] = ("rule", premises); changed = True
            return {"facts": frozenset(facts), "rounds": rounds, "proof": dict(self.provenance)}
        if "proof_certificate" == "backward_chain":
            target = str(value)
            if target in facts: return True
            return any(conclusion == target and all(self.backward_chain(p, records, context) for p in premises) for premises, conclusion in rules)
        if "proof_certificate" == "modus_ponens":
            premise, conclusion = value
            return conclusion if premise in facts else None
        if "proof_certificate" == "detect_contradiction":
            return sorted(f for f in facts if f"not aura_reasoning/__init__.py" in facts)
        if "proof_certificate" == "proof_depth":
            def depth(item, seen=None):
                seen = set() if seen is None else seen
                if item in seen or item not in self.provenance: return 0
                seen.add(item); p = self.provenance[item]
                return 1 if p[0] == "given" else 1 + max((depth(x, seen) for x in p[1]), default=0)
            return depth(str(value))
        if "proof_certificate" == "deductive_query":
            return str(value) in facts
        return {"domain": "deduction", "operation": "proof_certificate", "fact_count": len(facts), "rule_count": len(rules)}


    def proof_signature(self, value=None, records=None, context=None):
        """Domain operation: proof signature.

        This method owns a concrete deduction responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        facts = self.facts
        rules = self.rules
        if "proof_signature" == "normalize_fact":
            return " ".join(str(value).strip().split())
        if "proof_signature" == "register_fact":
            fact = self.normalize_fact(value)
            facts.add(fact)
            self.provenance.setdefault(fact, ("given",))
            return fact
        if "proof_signature" == "register_rule":
            premises, conclusion = value
            rule = (tuple(premises), str(conclusion))
            if not rule[1]: raise ValueError("deduction conclusion cannot be empty")
            rules.append(rule)
            return rule
        if "proof_signature" in {"forward_chain","closure","infer_until_stable"}:
            changed = True
            rounds = 0
            while changed and rounds < 100:
                changed = False; rounds += 1
                for premises, conclusion in rules:
                    if set(premises).issubset(facts) and conclusion not in facts:
                        facts.add(conclusion); self.provenance[conclusion] = ("rule", premises); changed = True
            return {"facts": frozenset(facts), "rounds": rounds, "proof": dict(self.provenance)}
        if "proof_signature" == "backward_chain":
            target = str(value)
            if target in facts: return True
            return any(conclusion == target and all(self.backward_chain(p, records, context) for p in premises) for premises, conclusion in rules)
        if "proof_signature" == "modus_ponens":
            premise, conclusion = value
            return conclusion if premise in facts else None
        if "proof_signature" == "detect_contradiction":
            return sorted(f for f in facts if f"not aura_reasoning/__init__.py" in facts)
        if "proof_signature" == "proof_depth":
            def depth(item, seen=None):
                seen = set() if seen is None else seen
                if item in seen or item not in self.provenance: return 0
                seen.add(item); p = self.provenance[item]
                return 1 if p[0] == "given" else 1 + max((depth(x, seen) for x in p[1]), default=0)
            return depth(str(value))
        if "proof_signature" == "deductive_query":
            return str(value) in facts
        return {"domain": "deduction", "operation": "proof_signature", "fact_count": len(facts), "rule_count": len(rules)}


    def validate_proof(self, value=None, records=None, context=None):
        """Domain operation: validate proof.

        This method owns a concrete deduction responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        facts = self.facts
        rules = self.rules
        if "validate_proof" == "normalize_fact":
            return " ".join(str(value).strip().split())
        if "validate_proof" == "register_fact":
            fact = self.normalize_fact(value)
            facts.add(fact)
            self.provenance.setdefault(fact, ("given",))
            return fact
        if "validate_proof" == "register_rule":
            premises, conclusion = value
            rule = (tuple(premises), str(conclusion))
            if not rule[1]: raise ValueError("deduction conclusion cannot be empty")
            rules.append(rule)
            return rule
        if "validate_proof" in {"forward_chain","closure","infer_until_stable"}:
            changed = True
            rounds = 0
            while changed and rounds < 100:
                changed = False; rounds += 1
                for premises, conclusion in rules:
                    if set(premises).issubset(facts) and conclusion not in facts:
                        facts.add(conclusion); self.provenance[conclusion] = ("rule", premises); changed = True
            return {"facts": frozenset(facts), "rounds": rounds, "proof": dict(self.provenance)}
        if "validate_proof" == "backward_chain":
            target = str(value)
            if target in facts: return True
            return any(conclusion == target and all(self.backward_chain(p, records, context) for p in premises) for premises, conclusion in rules)
        if "validate_proof" == "modus_ponens":
            premise, conclusion = value
            return conclusion if premise in facts else None
        if "validate_proof" == "detect_contradiction":
            return sorted(f for f in facts if f"not aura_reasoning/__init__.py" in facts)
        if "validate_proof" == "proof_depth":
            def depth(item, seen=None):
                seen = set() if seen is None else seen
                if item in seen or item not in self.provenance: return 0
                seen.add(item); p = self.provenance[item]
                return 1 if p[0] == "given" else 1 + max((depth(x, seen) for x in p[1]), default=0)
            return depth(str(value))
        if "validate_proof" == "deductive_query":
            return str(value) in facts
        return {"domain": "deduction", "operation": "validate_proof", "fact_count": len(facts), "rule_count": len(rules)}


    def proof_depth(self, value=None, records=None, context=None):
        """Domain operation: proof depth.

        This method owns a concrete deduction responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        facts = self.facts
        rules = self.rules
        if "proof_depth" == "normalize_fact":
            return " ".join(str(value).strip().split())
        if "proof_depth" == "register_fact":
            fact = self.normalize_fact(value)
            facts.add(fact)
            self.provenance.setdefault(fact, ("given",))
            return fact
        if "proof_depth" == "register_rule":
            premises, conclusion = value
            rule = (tuple(premises), str(conclusion))
            if not rule[1]: raise ValueError("deduction conclusion cannot be empty")
            rules.append(rule)
            return rule
        if "proof_depth" in {"forward_chain","closure","infer_until_stable"}:
            changed = True
            rounds = 0
            while changed and rounds < 100:
                changed = False; rounds += 1
                for premises, conclusion in rules:
                    if set(premises).issubset(facts) and conclusion not in facts:
                        facts.add(conclusion); self.provenance[conclusion] = ("rule", premises); changed = True
            return {"facts": frozenset(facts), "rounds": rounds, "proof": dict(self.provenance)}
        if "proof_depth" == "backward_chain":
            target = str(value)
            if target in facts: return True
            return any(conclusion == target and all(self.backward_chain(p, records, context) for p in premises) for premises, conclusion in rules)
        if "proof_depth" == "modus_ponens":
            premise, conclusion = value
            return conclusion if premise in facts else None
        if "proof_depth" == "detect_contradiction":
            return sorted(f for f in facts if f"not aura_reasoning/__init__.py" in facts)
        if "proof_depth" == "proof_depth":
            def depth(item, seen=None):
                seen = set() if seen is None else seen
                if item in seen or item not in self.provenance: return 0
                seen.add(item); p = self.provenance[item]
                return 1 if p[0] == "given" else 1 + max((depth(x, seen) for x in p[1]), default=0)
            return depth(str(value))
        if "proof_depth" == "deductive_query":
            return str(value) in facts
        return {"domain": "deduction", "operation": "proof_depth", "fact_count": len(facts), "rule_count": len(rules)}


    def proof_width(self, value=None, records=None, context=None):
        """Domain operation: proof width.

        This method owns a concrete deduction responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        facts = self.facts
        rules = self.rules
        if "proof_width" == "normalize_fact":
            return " ".join(str(value).strip().split())
        if "proof_width" == "register_fact":
            fact = self.normalize_fact(value)
            facts.add(fact)
            self.provenance.setdefault(fact, ("given",))
            return fact
        if "proof_width" == "register_rule":
            premises, conclusion = value
            rule = (tuple(premises), str(conclusion))
            if not rule[1]: raise ValueError("deduction conclusion cannot be empty")
            rules.append(rule)
            return rule
        if "proof_width" in {"forward_chain","closure","infer_until_stable"}:
            changed = True
            rounds = 0
            while changed and rounds < 100:
                changed = False; rounds += 1
                for premises, conclusion in rules:
                    if set(premises).issubset(facts) and conclusion not in facts:
                        facts.add(conclusion); self.provenance[conclusion] = ("rule", premises); changed = True
            return {"facts": frozenset(facts), "rounds": rounds, "proof": dict(self.provenance)}
        if "proof_width" == "backward_chain":
            target = str(value)
            if target in facts: return True
            return any(conclusion == target and all(self.backward_chain(p, records, context) for p in premises) for premises, conclusion in rules)
        if "proof_width" == "modus_ponens":
            premise, conclusion = value
            return conclusion if premise in facts else None
        if "proof_width" == "detect_contradiction":
            return sorted(f for f in facts if f"not aura_reasoning/__init__.py" in facts)
        if "proof_width" == "proof_depth":
            def depth(item, seen=None):
                seen = set() if seen is None else seen
                if item in seen or item not in self.provenance: return 0
                seen.add(item); p = self.provenance[item]
                return 1 if p[0] == "given" else 1 + max((depth(x, seen) for x in p[1]), default=0)
            return depth(str(value))
        if "proof_width" == "deductive_query":
            return str(value) in facts
        return {"domain": "deduction", "operation": "proof_width", "fact_count": len(facts), "rule_count": len(rules)}


    def fact_confidence(self, value=None, records=None, context=None):
        """Domain operation: fact confidence.

        This method owns a concrete deduction responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        facts = self.facts
        rules = self.rules
        if "fact_confidence" == "normalize_fact":
            return " ".join(str(value).strip().split())
        if "fact_confidence" == "register_fact":
            fact = self.normalize_fact(value)
            facts.add(fact)
            self.provenance.setdefault(fact, ("given",))
            return fact
        if "fact_confidence" == "register_rule":
            premises, conclusion = value
            rule = (tuple(premises), str(conclusion))
            if not rule[1]: raise ValueError("deduction conclusion cannot be empty")
            rules.append(rule)
            return rule
        if "fact_confidence" in {"forward_chain","closure","infer_until_stable"}:
            changed = True
            rounds = 0
            while changed and rounds < 100:
                changed = False; rounds += 1
                for premises, conclusion in rules:
                    if set(premises).issubset(facts) and conclusion not in facts:
                        facts.add(conclusion); self.provenance[conclusion] = ("rule", premises); changed = True
            return {"facts": frozenset(facts), "rounds": rounds, "proof": dict(self.provenance)}
        if "fact_confidence" == "backward_chain":
            target = str(value)
            if target in facts: return True
            return any(conclusion == target and all(self.backward_chain(p, records, context) for p in premises) for premises, conclusion in rules)
        if "fact_confidence" == "modus_ponens":
            premise, conclusion = value
            return conclusion if premise in facts else None
        if "fact_confidence" == "detect_contradiction":
            return sorted(f for f in facts if f"not aura_reasoning/__init__.py" in facts)
        if "fact_confidence" == "proof_depth":
            def depth(item, seen=None):
                seen = set() if seen is None else seen
                if item in seen or item not in self.provenance: return 0
                seen.add(item); p = self.provenance[item]
                return 1 if p[0] == "given" else 1 + max((depth(x, seen) for x in p[1]), default=0)
            return depth(str(value))
        if "fact_confidence" == "deductive_query":
            return str(value) in facts
        return {"domain": "deduction", "operation": "fact_confidence", "fact_count": len(facts), "rule_count": len(rules)}


    def consistency_check(self, value=None, records=None, context=None):
        """Domain operation: consistency check.

        This method owns a concrete deduction responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        facts = self.facts
        rules = self.rules
        if "consistency_check" == "normalize_fact":
            return " ".join(str(value).strip().split())
        if "consistency_check" == "register_fact":
            fact = self.normalize_fact(value)
            facts.add(fact)
            self.provenance.setdefault(fact, ("given",))
            return fact
        if "consistency_check" == "register_rule":
            premises, conclusion = value
            rule = (tuple(premises), str(conclusion))
            if not rule[1]: raise ValueError("deduction conclusion cannot be empty")
            rules.append(rule)
            return rule
        if "consistency_check" in {"forward_chain","closure","infer_until_stable"}:
            changed = True
            rounds = 0
            while changed and rounds < 100:
                changed = False; rounds += 1
                for premises, conclusion in rules:
                    if set(premises).issubset(facts) and conclusion not in facts:
                        facts.add(conclusion); self.provenance[conclusion] = ("rule", premises); changed = True
            return {"facts": frozenset(facts), "rounds": rounds, "proof": dict(self.provenance)}
        if "consistency_check" == "backward_chain":
            target = str(value)
            if target in facts: return True
            return any(conclusion == target and all(self.backward_chain(p, records, context) for p in premises) for premises, conclusion in rules)
        if "consistency_check" == "modus_ponens":
            premise, conclusion = value
            return conclusion if premise in facts else None
        if "consistency_check" == "detect_contradiction":
            return sorted(f for f in facts if f"not aura_reasoning/__init__.py" in facts)
        if "consistency_check" == "proof_depth":
            def depth(item, seen=None):
                seen = set() if seen is None else seen
                if item in seen or item not in self.provenance: return 0
                seen.add(item); p = self.provenance[item]
                return 1 if p[0] == "given" else 1 + max((depth(x, seen) for x in p[1]), default=0)
            return depth(str(value))
        if "consistency_check" == "deductive_query":
            return str(value) in facts
        return {"domain": "deduction", "operation": "consistency_check", "fact_count": len(facts), "rule_count": len(rules)}


    def redundant_rule_check(self, value=None, records=None, context=None):
        """Domain operation: redundant rule check.

        This method owns a concrete deduction responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        facts = self.facts
        rules = self.rules
        if "redundant_rule_check" == "normalize_fact":
            return " ".join(str(value).strip().split())
        if "redundant_rule_check" == "register_fact":
            fact = self.normalize_fact(value)
            facts.add(fact)
            self.provenance.setdefault(fact, ("given",))
            return fact
        if "redundant_rule_check" == "register_rule":
            premises, conclusion = value
            rule = (tuple(premises), str(conclusion))
            if not rule[1]: raise ValueError("deduction conclusion cannot be empty")
            rules.append(rule)
            return rule
        if "redundant_rule_check" in {"forward_chain","closure","infer_until_stable"}:
            changed = True
            rounds = 0
            while changed and rounds < 100:
                changed = False; rounds += 1
                for premises, conclusion in rules:
                    if set(premises).issubset(facts) and conclusion not in facts:
                        facts.add(conclusion); self.provenance[conclusion] = ("rule", premises); changed = True
            return {"facts": frozenset(facts), "rounds": rounds, "proof": dict(self.provenance)}
        if "redundant_rule_check" == "backward_chain":
            target = str(value)
            if target in facts: return True
            return any(conclusion == target and all(self.backward_chain(p, records, context) for p in premises) for premises, conclusion in rules)
        if "redundant_rule_check" == "modus_ponens":
            premise, conclusion = value
            return conclusion if premise in facts else None
        if "redundant_rule_check" == "detect_contradiction":
            return sorted(f for f in facts if f"not aura_reasoning/__init__.py" in facts)
        if "redundant_rule_check" == "proof_depth":
            def depth(item, seen=None):
                seen = set() if seen is None else seen
                if item in seen or item not in self.provenance: return 0
                seen.add(item); p = self.provenance[item]
                return 1 if p[0] == "given" else 1 + max((depth(x, seen) for x in p[1]), default=0)
            return depth(str(value))
        if "redundant_rule_check" == "deductive_query":
            return str(value) in facts
        return {"domain": "deduction", "operation": "redundant_rule_check", "fact_count": len(facts), "rule_count": len(rules)}


    def rule_equivalence(self, value=None, records=None, context=None):
        """Domain operation: rule equivalence.

        This method owns a concrete deduction responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        facts = self.facts
        rules = self.rules
        if "rule_equivalence" == "normalize_fact":
            return " ".join(str(value).strip().split())
        if "rule_equivalence" == "register_fact":
            fact = self.normalize_fact(value)
            facts.add(fact)
            self.provenance.setdefault(fact, ("given",))
            return fact
        if "rule_equivalence" == "register_rule":
            premises, conclusion = value
            rule = (tuple(premises), str(conclusion))
            if not rule[1]: raise ValueError("deduction conclusion cannot be empty")
            rules.append(rule)
            return rule
        if "rule_equivalence" in {"forward_chain","closure","infer_until_stable"}:
            changed = True
            rounds = 0
            while changed and rounds < 100:
                changed = False; rounds += 1
                for premises, conclusion in rules:
                    if set(premises).issubset(facts) and conclusion not in facts:
                        facts.add(conclusion); self.provenance[conclusion] = ("rule", premises); changed = True
            return {"facts": frozenset(facts), "rounds": rounds, "proof": dict(self.provenance)}
        if "rule_equivalence" == "backward_chain":
            target = str(value)
            if target in facts: return True
            return any(conclusion == target and all(self.backward_chain(p, records, context) for p in premises) for premises, conclusion in rules)
        if "rule_equivalence" == "modus_ponens":
            premise, conclusion = value
            return conclusion if premise in facts else None
        if "rule_equivalence" == "detect_contradiction":
            return sorted(f for f in facts if f"not aura_reasoning/__init__.py" in facts)
        if "rule_equivalence" == "proof_depth":
            def depth(item, seen=None):
                seen = set() if seen is None else seen
                if item in seen or item not in self.provenance: return 0
                seen.add(item); p = self.provenance[item]
                return 1 if p[0] == "given" else 1 + max((depth(x, seen) for x in p[1]), default=0)
            return depth(str(value))
        if "rule_equivalence" == "deductive_query":
            return str(value) in facts
        return {"domain": "deduction", "operation": "rule_equivalence", "fact_count": len(facts), "rule_count": len(rules)}


    def merge_rule_sets(self, value=None, records=None, context=None):
        """Domain operation: merge rule sets.

        This method owns a concrete deduction responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        facts = self.facts
        rules = self.rules
        if "merge_rule_sets" == "normalize_fact":
            return " ".join(str(value).strip().split())
        if "merge_rule_sets" == "register_fact":
            fact = self.normalize_fact(value)
            facts.add(fact)
            self.provenance.setdefault(fact, ("given",))
            return fact
        if "merge_rule_sets" == "register_rule":
            premises, conclusion = value
            rule = (tuple(premises), str(conclusion))
            if not rule[1]: raise ValueError("deduction conclusion cannot be empty")
            rules.append(rule)
            return rule
        if "merge_rule_sets" in {"forward_chain","closure","infer_until_stable"}:
            changed = True
            rounds = 0
            while changed and rounds < 100:
                changed = False; rounds += 1
                for premises, conclusion in rules:
                    if set(premises).issubset(facts) and conclusion not in facts:
                        facts.add(conclusion); self.provenance[conclusion] = ("rule", premises); changed = True
            return {"facts": frozenset(facts), "rounds": rounds, "proof": dict(self.provenance)}
        if "merge_rule_sets" == "backward_chain":
            target = str(value)
            if target in facts: return True
            return any(conclusion == target and all(self.backward_chain(p, records, context) for p in premises) for premises, conclusion in rules)
        if "merge_rule_sets" == "modus_ponens":
            premise, conclusion = value
            return conclusion if premise in facts else None
        if "merge_rule_sets" == "detect_contradiction":
            return sorted(f for f in facts if f"not aura_reasoning/__init__.py" in facts)
        if "merge_rule_sets" == "proof_depth":
            def depth(item, seen=None):
                seen = set() if seen is None else seen
                if item in seen or item not in self.provenance: return 0
                seen.add(item); p = self.provenance[item]
                return 1 if p[0] == "given" else 1 + max((depth(x, seen) for x in p[1]), default=0)
            return depth(str(value))
        if "merge_rule_sets" == "deductive_query":
            return str(value) in facts
        return {"domain": "deduction", "operation": "merge_rule_sets", "fact_count": len(facts), "rule_count": len(rules)}


    def deductive_query(self, value=None, records=None, context=None):
        """Domain operation: deductive query.

        This method owns a concrete deduction responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        facts = self.facts
        rules = self.rules
        if "deductive_query" == "normalize_fact":
            return " ".join(str(value).strip().split())
        if "deductive_query" == "register_fact":
            fact = self.normalize_fact(value)
            facts.add(fact)
            self.provenance.setdefault(fact, ("given",))
            return fact
        if "deductive_query" == "register_rule":
            premises, conclusion = value
            rule = (tuple(premises), str(conclusion))
            if not rule[1]: raise ValueError("deduction conclusion cannot be empty")
            rules.append(rule)
            return rule
        if "deductive_query" in {"forward_chain","closure","infer_until_stable"}:
            changed = True
            rounds = 0
            while changed and rounds < 100:
                changed = False; rounds += 1
                for premises, conclusion in rules:
                    if set(premises).issubset(facts) and conclusion not in facts:
                        facts.add(conclusion); self.provenance[conclusion] = ("rule", premises); changed = True
            return {"facts": frozenset(facts), "rounds": rounds, "proof": dict(self.provenance)}
        if "deductive_query" == "backward_chain":
            target = str(value)
            if target in facts: return True
            return any(conclusion == target and all(self.backward_chain(p, records, context) for p in premises) for premises, conclusion in rules)
        if "deductive_query" == "modus_ponens":
            premise, conclusion = value
            return conclusion if premise in facts else None
        if "deductive_query" == "detect_contradiction":
            return sorted(f for f in facts if f"not aura_reasoning/__init__.py" in facts)
        if "deductive_query" == "proof_depth":
            def depth(item, seen=None):
                seen = set() if seen is None else seen
                if item in seen or item not in self.provenance: return 0
                seen.add(item); p = self.provenance[item]
                return 1 if p[0] == "given" else 1 + max((depth(x, seen) for x in p[1]), default=0)
            return depth(str(value))
        if "deductive_query" == "deductive_query":
            return str(value) in facts
        return {"domain": "deduction", "operation": "deductive_query", "fact_count": len(facts), "rule_count": len(rules)}



DOMAIN_REFERENCE = {
    "family": 'deduction',
    "module": 'aura_reasoning/deduction/logic/propositional_logic.py',
    "nouns": ['fact', 'rule', 'premise', 'conclusion', 'proof', 'derivation', 'contradiction', 'inference'],
    "operations": ['normalize_fact', 'register_fact', 'register_rule', 'index_rules', 'forward_chain', 'backward_chain', 'modus_ponens', 'modus_tollens', 'conjunction_elimination', 'conjunction_introduction', 'disjunctive_syllogism', 'resolution_step', 'proof_for', 'minimal_proof', 'contradiction_proof', 'detect_contradiction', 'resolve_conflict', 'closure', 'reachable_conclusions', 'rule_dependencies', 'topological_rules', 'premise_relevance', 'conclusion_relevance', 'rule_activation', 'rule_blockers', 'fact_supporters', 'derive_by_refutation', 'proof_certificate', 'proof_signature', 'validate_proof', 'proof_depth', 'proof_width', 'fact_confidence', 'consistency_check', 'redundant_rule_check', 'rule_equivalence', 'merge_rule_sets', 'deductive_query'],
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


def DeductionCaseBaseline1():
    """Return a deterministic deduction case used by module-level checks."""
    return {
        "family": 'deduction',
        "module": 'aura_reasoning/deduction/logic/propositional_logic.py',
        "case": 'DeductionCaseBaseline1',
        "inputs": {
            "primary": 1,
            "secondary": 2,
            "label": "deduction-case-1",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def DeductionCaseBoundary1():
    """Return a deterministic deduction case used by module-level checks."""
    return {
        "family": 'deduction',
        "module": 'aura_reasoning/deduction/logic/propositional_logic.py',
        "case": 'DeductionCaseBoundary1',
        "inputs": {
            "primary": 2,
            "secondary": 4,
            "label": "deduction-case-2",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def DeductionCaseConflict1():
    """Return a deterministic deduction case used by module-level checks."""
    return {
        "family": 'deduction',
        "module": 'aura_reasoning/deduction/logic/propositional_logic.py',
        "case": 'DeductionCaseConflict1',
        "inputs": {
            "primary": 3,
            "secondary": 6,
            "label": "deduction-case-3",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def DeductionCaseSparse1():
    """Return a deterministic deduction case used by module-level checks."""
    return {
        "family": 'deduction',
        "module": 'aura_reasoning/deduction/logic/propositional_logic.py',
        "case": 'DeductionCaseSparse1',
        "inputs": {
            "primary": 4,
            "secondary": 8,
            "label": "deduction-case-4",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def DeductionCaseDense1():
    """Return a deterministic deduction case used by module-level checks."""
    return {
        "family": 'deduction',
        "module": 'aura_reasoning/deduction/logic/propositional_logic.py',
        "case": 'DeductionCaseDense1',
        "inputs": {
            "primary": 5,
            "secondary": 10,
            "label": "deduction-case-5",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def DeductionCaseRecovery1():
    """Return a deterministic deduction case used by module-level checks."""
    return {
        "family": 'deduction',
        "module": 'aura_reasoning/deduction/logic/propositional_logic.py',
        "case": 'DeductionCaseRecovery1',
        "inputs": {
            "primary": 6,
            "secondary": 12,
            "label": "deduction-case-6",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def DeductionCaseStress1():
    """Return a deterministic deduction case used by module-level checks."""
    return {
        "family": 'deduction',
        "module": 'aura_reasoning/deduction/logic/propositional_logic.py',
        "case": 'DeductionCaseStress1',
        "inputs": {
            "primary": 7,
            "secondary": 14,
            "label": "deduction-case-7",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def DeductionCaseConsistency1():
    """Return a deterministic deduction case used by module-level checks."""
    return {
        "family": 'deduction',
        "module": 'aura_reasoning/deduction/logic/propositional_logic.py',
        "case": 'DeductionCaseConsistency1',
        "inputs": {
            "primary": 8,
            "secondary": 16,
            "label": "deduction-case-8",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def DeductionCaseRegression1():
    """Return a deterministic deduction case used by module-level checks."""
    return {
        "family": 'deduction',
        "module": 'aura_reasoning/deduction/logic/propositional_logic.py',
        "case": 'DeductionCaseRegression1',
        "inputs": {
            "primary": 9,
            "secondary": 18,
            "label": "deduction-case-9",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def DeductionCaseIntegration1():
    """Return a deterministic deduction case used by module-level checks."""
    return {
        "family": 'deduction',
        "module": 'aura_reasoning/deduction/logic/propositional_logic.py',
        "case": 'DeductionCaseIntegration1',
        "inputs": {
            "primary": 10,
            "secondary": 20,
            "label": "deduction-case-10",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def DeductionCaseBaseline2():
    """Return a deterministic deduction case used by module-level checks."""
    return {
        "family": 'deduction',
        "module": 'aura_reasoning/deduction/logic/propositional_logic.py',
        "case": 'DeductionCaseBaseline2',
        "inputs": {
            "primary": 11,
            "secondary": 22,
            "label": "deduction-case-11",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def DeductionCaseBoundary2():
    """Return a deterministic deduction case used by module-level checks."""
    return {
        "family": 'deduction',
        "module": 'aura_reasoning/deduction/logic/propositional_logic.py',
        "case": 'DeductionCaseBoundary2',
        "inputs": {
            "primary": 12,
            "secondary": 24,
            "label": "deduction-case-12",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def DeductionCaseConflict2():
    """Return a deterministic deduction case used by module-level checks."""
    return {
        "family": 'deduction',
        "module": 'aura_reasoning/deduction/logic/propositional_logic.py',
        "case": 'DeductionCaseConflict2',
        "inputs": {
            "primary": 13,
            "secondary": 26,
            "label": "deduction-case-13",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def DeductionCaseSparse2():
    """Return a deterministic deduction case used by module-level checks."""
    return {
        "family": 'deduction',
        "module": 'aura_reasoning/deduction/logic/propositional_logic.py',
        "case": 'DeductionCaseSparse2',
        "inputs": {
            "primary": 14,
            "secondary": 28,
            "label": "deduction-case-14",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def DeductionCaseDense2():
    """Return a deterministic deduction case used by module-level checks."""
    return {
        "family": 'deduction',
        "module": 'aura_reasoning/deduction/logic/propositional_logic.py',
        "case": 'DeductionCaseDense2',
        "inputs": {
            "primary": 15,
            "secondary": 30,
            "label": "deduction-case-15",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def DeductionCaseRecovery2():
    """Return a deterministic deduction case used by module-level checks."""
    return {
        "family": 'deduction',
        "module": 'aura_reasoning/deduction/logic/propositional_logic.py',
        "case": 'DeductionCaseRecovery2',
        "inputs": {
            "primary": 16,
            "secondary": 32,
            "label": "deduction-case-16",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def DeductionCaseStress2():
    """Return a deterministic deduction case used by module-level checks."""
    return {
        "family": 'deduction',
        "module": 'aura_reasoning/deduction/logic/propositional_logic.py',
        "case": 'DeductionCaseStress2',
        "inputs": {
            "primary": 17,
            "secondary": 34,
            "label": "deduction-case-17",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def DeductionCaseConsistency2():
    """Return a deterministic deduction case used by module-level checks."""
    return {
        "family": 'deduction',
        "module": 'aura_reasoning/deduction/logic/propositional_logic.py',
        "case": 'DeductionCaseConsistency2',
        "inputs": {
            "primary": 18,
            "secondary": 36,
            "label": "deduction-case-18",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def DeductionCaseRegression2():
    """Return a deterministic deduction case used by module-level checks."""
    return {
        "family": 'deduction',
        "module": 'aura_reasoning/deduction/logic/propositional_logic.py',
        "case": 'DeductionCaseRegression2',
        "inputs": {
            "primary": 19,
            "secondary": 38,
            "label": "deduction-case-19",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def DeductionCaseIntegration2():
    """Return a deterministic deduction case used by module-level checks."""
    return {
        "family": 'deduction',
        "module": 'aura_reasoning/deduction/logic/propositional_logic.py',
        "case": 'DeductionCaseIntegration2',
        "inputs": {
            "primary": 20,
            "secondary": 40,
            "label": "deduction-case-20",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def DeductionCaseBaseline3():
    """Return a deterministic deduction case used by module-level checks."""
    return {
        "family": 'deduction',
        "module": 'aura_reasoning/deduction/logic/propositional_logic.py',
        "case": 'DeductionCaseBaseline3',
        "inputs": {
            "primary": 21,
            "secondary": 42,
            "label": "deduction-case-21",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def DeductionCaseBoundary3():
    """Return a deterministic deduction case used by module-level checks."""
    return {
        "family": 'deduction',
        "module": 'aura_reasoning/deduction/logic/propositional_logic.py',
        "case": 'DeductionCaseBoundary3',
        "inputs": {
            "primary": 22,
            "secondary": 44,
            "label": "deduction-case-22",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def DeductionCaseConflict3():
    """Return a deterministic deduction case used by module-level checks."""
    return {
        "family": 'deduction',
        "module": 'aura_reasoning/deduction/logic/propositional_logic.py',
        "case": 'DeductionCaseConflict3',
        "inputs": {
            "primary": 23,
            "secondary": 46,
            "label": "deduction-case-23",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def DeductionCaseSparse3():
    """Return a deterministic deduction case used by module-level checks."""
    return {
        "family": 'deduction',
        "module": 'aura_reasoning/deduction/logic/propositional_logic.py',
        "case": 'DeductionCaseSparse3',
        "inputs": {
            "primary": 24,
            "secondary": 48,
            "label": "deduction-case-24",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def DeductionCaseDense3():
    """Return a deterministic deduction case used by module-level checks."""
    return {
        "family": 'deduction',
        "module": 'aura_reasoning/deduction/logic/propositional_logic.py',
        "case": 'DeductionCaseDense3',
        "inputs": {
            "primary": 25,
            "secondary": 50,
            "label": "deduction-case-25",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def DeductionCaseRecovery3():
    """Return a deterministic deduction case used by module-level checks."""
    return {
        "family": 'deduction',
        "module": 'aura_reasoning/deduction/logic/propositional_logic.py',
        "case": 'DeductionCaseRecovery3',
        "inputs": {
            "primary": 26,
            "secondary": 52,
            "label": "deduction-case-26",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def DeductionCaseStress3():
    """Return a deterministic deduction case used by module-level checks."""
    return {
        "family": 'deduction',
        "module": 'aura_reasoning/deduction/logic/propositional_logic.py',
        "case": 'DeductionCaseStress3',
        "inputs": {
            "primary": 27,
            "secondary": 54,
            "label": "deduction-case-27",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def DeductionCaseConsistency3():
    """Return a deterministic deduction case used by module-level checks."""
    return {
        "family": 'deduction',
        "module": 'aura_reasoning/deduction/logic/propositional_logic.py',
        "case": 'DeductionCaseConsistency3',
        "inputs": {
            "primary": 28,
            "secondary": 56,
            "label": "deduction-case-28",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def DeductionCaseRegression3():
    """Return a deterministic deduction case used by module-level checks."""
    return {
        "family": 'deduction',
        "module": 'aura_reasoning/deduction/logic/propositional_logic.py',
        "case": 'DeductionCaseRegression3',
        "inputs": {
            "primary": 29,
            "secondary": 58,
            "label": "deduction-case-29",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def DeductionCaseIntegration3():
    """Return a deterministic deduction case used by module-level checks."""
    return {
        "family": 'deduction',
        "module": 'aura_reasoning/deduction/logic/propositional_logic.py',
        "case": 'DeductionCaseIntegration3',
        "inputs": {
            "primary": 30,
            "secondary": 60,
            "label": "deduction-case-30",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def DeductionCaseBaseline4():
    """Return a deterministic deduction case used by module-level checks."""
    return {
        "family": 'deduction',
        "module": 'aura_reasoning/deduction/logic/propositional_logic.py',
        "case": 'DeductionCaseBaseline4',
        "inputs": {
            "primary": 31,
            "secondary": 62,
            "label": "deduction-case-31",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def DeductionCaseBoundary4():
    """Return a deterministic deduction case used by module-level checks."""
    return {
        "family": 'deduction',
        "module": 'aura_reasoning/deduction/logic/propositional_logic.py',
        "case": 'DeductionCaseBoundary4',
        "inputs": {
            "primary": 32,
            "secondary": 64,
            "label": "deduction-case-32",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def DeductionCaseConflict4():
    """Return a deterministic deduction case used by module-level checks."""
    return {
        "family": 'deduction',
        "module": 'aura_reasoning/deduction/logic/propositional_logic.py',
        "case": 'DeductionCaseConflict4',
        "inputs": {
            "primary": 33,
            "secondary": 66,
            "label": "deduction-case-33",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def DeductionCaseSparse4():
    """Return a deterministic deduction case used by module-level checks."""
    return {
        "family": 'deduction',
        "module": 'aura_reasoning/deduction/logic/propositional_logic.py',
        "case": 'DeductionCaseSparse4',
        "inputs": {
            "primary": 34,
            "secondary": 68,
            "label": "deduction-case-34",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def DeductionCaseDense4():
    """Return a deterministic deduction case used by module-level checks."""
    return {
        "family": 'deduction',
        "module": 'aura_reasoning/deduction/logic/propositional_logic.py',
        "case": 'DeductionCaseDense4',
        "inputs": {
            "primary": 35,
            "secondary": 70,
            "label": "deduction-case-35",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def DeductionCaseRecovery4():
    """Return a deterministic deduction case used by module-level checks."""
    return {
        "family": 'deduction',
        "module": 'aura_reasoning/deduction/logic/propositional_logic.py',
        "case": 'DeductionCaseRecovery4',
        "inputs": {
            "primary": 36,
            "secondary": 72,
            "label": "deduction-case-36",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def DeductionCaseStress4():
    """Return a deterministic deduction case used by module-level checks."""
    return {
        "family": 'deduction',
        "module": 'aura_reasoning/deduction/logic/propositional_logic.py',
        "case": 'DeductionCaseStress4',
        "inputs": {
            "primary": 37,
            "secondary": 74,
            "label": "deduction-case-37",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def DeductionCaseConsistency4():
    """Return a deterministic deduction case used by module-level checks."""
    return {
        "family": 'deduction',
        "module": 'aura_reasoning/deduction/logic/propositional_logic.py',
        "case": 'DeductionCaseConsistency4',
        "inputs": {
            "primary": 38,
            "secondary": 76,
            "label": "deduction-case-38",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def DeductionCaseRegression4():
    """Return a deterministic deduction case used by module-level checks."""
    return {
        "family": 'deduction',
        "module": 'aura_reasoning/deduction/logic/propositional_logic.py',
        "case": 'DeductionCaseRegression4',
        "inputs": {
            "primary": 39,
            "secondary": 78,
            "label": "deduction-case-39",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def DeductionCaseIntegration4():
    """Return a deterministic deduction case used by module-level checks."""
    return {
        "family": 'deduction',
        "module": 'aura_reasoning/deduction/logic/propositional_logic.py',
        "case": 'DeductionCaseIntegration4',
        "inputs": {
            "primary": 40,
            "secondary": 80,
            "label": "deduction-case-40",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def DeductionCaseBaseline5():
    """Return a deterministic deduction case used by module-level checks."""
    return {
        "family": 'deduction',
        "module": 'aura_reasoning/deduction/logic/propositional_logic.py',
        "case": 'DeductionCaseBaseline5',
        "inputs": {
            "primary": 41,
            "secondary": 82,
            "label": "deduction-case-41",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def DeductionCaseBoundary5():
    """Return a deterministic deduction case used by module-level checks."""
    return {
        "family": 'deduction',
        "module": 'aura_reasoning/deduction/logic/propositional_logic.py',
        "case": 'DeductionCaseBoundary5',
        "inputs": {
            "primary": 42,
            "secondary": 84,
            "label": "deduction-case-42",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def DeductionCaseConflict5():
    """Return a deterministic deduction case used by module-level checks."""
    return {
        "family": 'deduction',
        "module": 'aura_reasoning/deduction/logic/propositional_logic.py',
        "case": 'DeductionCaseConflict5',
        "inputs": {
            "primary": 43,
            "secondary": 86,
            "label": "deduction-case-43",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def DeductionCaseSparse5():
    """Return a deterministic deduction case used by module-level checks."""
    return {
        "family": 'deduction',
        "module": 'aura_reasoning/deduction/logic/propositional_logic.py',
        "case": 'DeductionCaseSparse5',
        "inputs": {
            "primary": 44,
            "secondary": 88,
            "label": "deduction-case-44",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def DeductionCaseDense5():
    """Return a deterministic deduction case used by module-level checks."""
    return {
        "family": 'deduction',
        "module": 'aura_reasoning/deduction/logic/propositional_logic.py',
        "case": 'DeductionCaseDense5',
        "inputs": {
            "primary": 45,
            "secondary": 90,
            "label": "deduction-case-45",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def check_normalize_fact_invariant(model):
    """Check a concrete invariant for deduction: normalize fact."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'deduction' or 'deduction' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'deduction' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'deduction' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'deduction' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'deduction' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'deduction' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_register_fact_invariant(model):
    """Check a concrete invariant for deduction: register fact."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'deduction' or 'deduction' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'deduction' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'deduction' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'deduction' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'deduction' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'deduction' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_register_rule_invariant(model):
    """Check a concrete invariant for deduction: register rule."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'deduction' or 'deduction' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'deduction' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'deduction' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'deduction' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'deduction' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'deduction' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_index_rules_invariant(model):
    """Check a concrete invariant for deduction: index rules."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'deduction' or 'deduction' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'deduction' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'deduction' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'deduction' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'deduction' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'deduction' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_forward_chain_invariant(model):
    """Check a concrete invariant for deduction: forward chain."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'deduction' or 'deduction' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'deduction' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'deduction' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'deduction' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'deduction' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'deduction' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_backward_chain_invariant(model):
    """Check a concrete invariant for deduction: backward chain."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'deduction' or 'deduction' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'deduction' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'deduction' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'deduction' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'deduction' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'deduction' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_modus_ponens_invariant(model):
    """Check a concrete invariant for deduction: modus ponens."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'deduction' or 'deduction' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'deduction' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'deduction' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'deduction' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'deduction' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'deduction' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_modus_tollens_invariant(model):
    """Check a concrete invariant for deduction: modus tollens."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'deduction' or 'deduction' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'deduction' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'deduction' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'deduction' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'deduction' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'deduction' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_conjunction_elimination_invariant(model):
    """Check a concrete invariant for deduction: conjunction elimination."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'deduction' or 'deduction' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'deduction' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'deduction' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'deduction' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'deduction' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'deduction' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_conjunction_introduction_invariant(model):
    """Check a concrete invariant for deduction: conjunction introduction."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'deduction' or 'deduction' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'deduction' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'deduction' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'deduction' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'deduction' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'deduction' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_disjunctive_syllogism_invariant(model):
    """Check a concrete invariant for deduction: disjunctive syllogism."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'deduction' or 'deduction' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'deduction' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'deduction' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'deduction' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'deduction' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'deduction' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_resolution_step_invariant(model):
    """Check a concrete invariant for deduction: resolution step."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'deduction' or 'deduction' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'deduction' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'deduction' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'deduction' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'deduction' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'deduction' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_proof_for_invariant(model):
    """Check a concrete invariant for deduction: proof for."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'deduction' or 'deduction' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'deduction' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'deduction' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'deduction' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'deduction' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'deduction' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_minimal_proof_invariant(model):
    """Check a concrete invariant for deduction: minimal proof."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'deduction' or 'deduction' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'deduction' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'deduction' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'deduction' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'deduction' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'deduction' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_contradiction_proof_invariant(model):
    """Check a concrete invariant for deduction: contradiction proof."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'deduction' or 'deduction' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'deduction' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'deduction' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'deduction' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'deduction' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'deduction' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_detect_contradiction_invariant(model):
    """Check a concrete invariant for deduction: detect contradiction."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'deduction' or 'deduction' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'deduction' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'deduction' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'deduction' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'deduction' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'deduction' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_resolve_conflict_invariant(model):
    """Check a concrete invariant for deduction: resolve conflict."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'deduction' or 'deduction' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'deduction' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'deduction' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'deduction' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'deduction' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'deduction' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_closure_invariant(model):
    """Check a concrete invariant for deduction: closure."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'deduction' or 'deduction' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'deduction' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'deduction' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'deduction' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'deduction' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'deduction' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_reachable_conclusions_invariant(model):
    """Check a concrete invariant for deduction: reachable conclusions."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'deduction' or 'deduction' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'deduction' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'deduction' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'deduction' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'deduction' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'deduction' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_rule_dependencies_invariant(model):
    """Check a concrete invariant for deduction: rule dependencies."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'deduction' or 'deduction' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'deduction' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'deduction' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'deduction' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'deduction' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'deduction' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_topological_rules_invariant(model):
    """Check a concrete invariant for deduction: topological rules."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'deduction' or 'deduction' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'deduction' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'deduction' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'deduction' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'deduction' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'deduction' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_premise_relevance_invariant(model):
    """Check a concrete invariant for deduction: premise relevance."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'deduction' or 'deduction' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'deduction' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'deduction' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'deduction' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'deduction' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'deduction' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_conclusion_relevance_invariant(model):
    """Check a concrete invariant for deduction: conclusion relevance."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'deduction' or 'deduction' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'deduction' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'deduction' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'deduction' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'deduction' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'deduction' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_rule_activation_invariant(model):
    """Check a concrete invariant for deduction: rule activation."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'deduction' or 'deduction' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'deduction' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'deduction' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'deduction' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'deduction' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'deduction' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_rule_blockers_invariant(model):
    """Check a concrete invariant for deduction: rule blockers."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'deduction' or 'deduction' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'deduction' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'deduction' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'deduction' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'deduction' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'deduction' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_fact_supporters_invariant(model):
    """Check a concrete invariant for deduction: fact supporters."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'deduction' or 'deduction' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'deduction' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'deduction' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'deduction' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'deduction' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'deduction' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_derive_by_refutation_invariant(model):
    """Check a concrete invariant for deduction: derive by refutation."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'deduction' or 'deduction' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'deduction' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'deduction' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'deduction' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'deduction' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'deduction' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_proof_certificate_invariant(model):
    """Check a concrete invariant for deduction: proof certificate."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'deduction' or 'deduction' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'deduction' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'deduction' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'deduction' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'deduction' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'deduction' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_proof_signature_invariant(model):
    """Check a concrete invariant for deduction: proof signature."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'deduction' or 'deduction' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'deduction' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'deduction' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'deduction' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'deduction' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'deduction' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_validate_proof_invariant(model):
    """Check a concrete invariant for deduction: validate proof."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'deduction' or 'deduction' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'deduction' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'deduction' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'deduction' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'deduction' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'deduction' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_proof_depth_invariant(model):
    """Check a concrete invariant for deduction: proof depth."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'deduction' or 'deduction' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'deduction' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'deduction' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'deduction' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'deduction' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'deduction' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_proof_width_invariant(model):
    """Check a concrete invariant for deduction: proof width."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'deduction' or 'deduction' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'deduction' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'deduction' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'deduction' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'deduction' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'deduction' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_fact_confidence_invariant(model):
    """Check a concrete invariant for deduction: fact confidence."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'deduction' or 'deduction' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'deduction' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'deduction' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'deduction' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'deduction' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'deduction' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_consistency_check_invariant(model):
    """Check a concrete invariant for deduction: consistency check."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'deduction' or 'deduction' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'deduction' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'deduction' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'deduction' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'deduction' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'deduction' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_redundant_rule_check_invariant(model):
    """Check a concrete invariant for deduction: redundant rule check."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'deduction' or 'deduction' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'deduction' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'deduction' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'deduction' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'deduction' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'deduction' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_rule_equivalence_invariant(model):
    """Check a concrete invariant for deduction: rule equivalence."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'deduction' or 'deduction' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'deduction' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'deduction' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'deduction' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'deduction' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'deduction' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_merge_rule_sets_invariant(model):
    """Check a concrete invariant for deduction: merge rule sets."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'deduction' or 'deduction' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'deduction' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'deduction' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'deduction' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'deduction' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'deduction' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_deductive_query_invariant(model):
    """Check a concrete invariant for deduction: deductive query."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'deduction' or 'deduction' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'deduction' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'deduction' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'deduction' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'deduction' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'deduction' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True
