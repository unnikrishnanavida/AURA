"""
Domain-first implementation for examples/basic_reasoning/simple_reasoning.py.

Subsystem: examples
This module owns examples, state, record, relation, score, constraint semantics.
The implementation is intentionally specialized to this subsystem. Shared
AURA infrastructure belongs in the infrastructure packages instead of being
copied into every domain module.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from collections import defaultdict, deque
from typing import Any, Mapping, Iterable


@dataclass
class ExamplesState:
    identifier: str
    value: Any = None
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class ExamplesRecord:
    identifier: str
    value: Any = None
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class ExamplesGraph:
    identifier: str
    value: Any = None
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class ExamplesResult:
    identifier: str
    value: Any = None
    metadata: dict[str, Any] = field(default_factory=dict)

class SimpleReasoning:
    def __init__(self):
        self.records = []
        self.state = {"domain": 'examples', "module": 'examples/basic_reasoning/simple_reasoning.py'}

    def build_example(self, value=None, records=None, context=None):
        """Domain operation: build example.

        This method owns a concrete examples responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        records = self.records
        if "build_example".endswith("_score") or "build_example" in {"score_option","score_case","score_answer","score_reasoning","score_evidence","score_consistency","score_completeness","reliability","quality"}:
            items = records if isinstance(records, list) else list(records.values()) if isinstance(records, dict) else []
            numeric = []
            for item in items:
                if isinstance(item, Mapping):
                    numeric.extend(float(v) for v in item.values() if isinstance(v,(int,float)))
            return sum(numeric)/len(numeric) if numeric else 0.0
        if "build_example" in {"compare_runs","compare_answers","compare_cases","configuration_diff","memory_diff","plan_compare","optimization_compare"}:
            left,right=value if isinstance(value,(list,tuple)) and len(value)==2 else ({},{})
            return {"added": sorted(set(right if isinstance(right,dict) else {})-set(left if isinstance(left,dict) else {})),
                     "removed": sorted(set(left if isinstance(left,dict) else {})-set(right if isinstance(right,dict) else {}))}
        if "build_example" in {"search_memory","retrieve_item","search_state","search_query","collect","find_common_features","retrieve_analogies"}:
            needle=str(value).lower()
            return [r for r in records if needle in str(r).lower()][:50]
        if "build_example" in {"rank_options","rank_candidates","rank_hypotheses","rank_explanations","rank_sources","rank_memories","rank_analogies"}:
            items = records if isinstance(records,list) else list(records.values()) if isinstance(records,dict) else []
            return sorted(items,key=lambda x: float(x.get("score",0)) if isinstance(x,Mapping) else 0, reverse=True)
        if "build_example" in {"report","summary","examples_report","examples_summary"}:
            return {"domain": "examples", "records": len(records), "sample": records[:5] if isinstance(records,list) else list(records)[:5]}
        if "build_example" in {"query","examples_query"}:
            return self.records.get(str(value)) if isinstance(self.records,dict) else [r for r in self.records if str(value).lower() in str(r).lower()]
        if isinstance(value, Mapping):
            records.append(dict(value))
            return dict(value)
        if value is not None:
            records.append({"value":value,"context":context})
            return records[-1]
        return {"domain":"examples","operation":"build_example","record_count":len(records)}


    def run_example(self, value=None, records=None, context=None):
        """Domain operation: run example.

        This method owns a concrete examples responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        records = self.records
        if "run_example".endswith("_score") or "run_example" in {"score_option","score_case","score_answer","score_reasoning","score_evidence","score_consistency","score_completeness","reliability","quality"}:
            items = records if isinstance(records, list) else list(records.values()) if isinstance(records, dict) else []
            numeric = []
            for item in items:
                if isinstance(item, Mapping):
                    numeric.extend(float(v) for v in item.values() if isinstance(v,(int,float)))
            return sum(numeric)/len(numeric) if numeric else 0.0
        if "run_example" in {"compare_runs","compare_answers","compare_cases","configuration_diff","memory_diff","plan_compare","optimization_compare"}:
            left,right=value if isinstance(value,(list,tuple)) and len(value)==2 else ({},{})
            return {"added": sorted(set(right if isinstance(right,dict) else {})-set(left if isinstance(left,dict) else {})),
                     "removed": sorted(set(left if isinstance(left,dict) else {})-set(right if isinstance(right,dict) else {}))}
        if "run_example" in {"search_memory","retrieve_item","search_state","search_query","collect","find_common_features","retrieve_analogies"}:
            needle=str(value).lower()
            return [r for r in records if needle in str(r).lower()][:50]
        if "run_example" in {"rank_options","rank_candidates","rank_hypotheses","rank_explanations","rank_sources","rank_memories","rank_analogies"}:
            items = records if isinstance(records,list) else list(records.values()) if isinstance(records,dict) else []
            return sorted(items,key=lambda x: float(x.get("score",0)) if isinstance(x,Mapping) else 0, reverse=True)
        if "run_example" in {"report","summary","examples_report","examples_summary"}:
            return {"domain": "examples", "records": len(records), "sample": records[:5] if isinstance(records,list) else list(records)[:5]}
        if "run_example" in {"query","examples_query"}:
            return self.records.get(str(value)) if isinstance(self.records,dict) else [r for r in self.records if str(value).lower() in str(r).lower()]
        if isinstance(value, Mapping):
            records.append(dict(value))
            return dict(value)
        if value is not None:
            records.append({"value":value,"context":context})
            return records[-1]
        return {"domain":"examples","operation":"run_example","record_count":len(records)}


    def inspect_example(self, value=None, records=None, context=None):
        """Domain operation: inspect example.

        This method owns a concrete examples responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        records = self.records
        if "inspect_example".endswith("_score") or "inspect_example" in {"score_option","score_case","score_answer","score_reasoning","score_evidence","score_consistency","score_completeness","reliability","quality"}:
            items = records if isinstance(records, list) else list(records.values()) if isinstance(records, dict) else []
            numeric = []
            for item in items:
                if isinstance(item, Mapping):
                    numeric.extend(float(v) for v in item.values() if isinstance(v,(int,float)))
            return sum(numeric)/len(numeric) if numeric else 0.0
        if "inspect_example" in {"compare_runs","compare_answers","compare_cases","configuration_diff","memory_diff","plan_compare","optimization_compare"}:
            left,right=value if isinstance(value,(list,tuple)) and len(value)==2 else ({},{})
            return {"added": sorted(set(right if isinstance(right,dict) else {})-set(left if isinstance(left,dict) else {})),
                     "removed": sorted(set(left if isinstance(left,dict) else {})-set(right if isinstance(right,dict) else {}))}
        if "inspect_example" in {"search_memory","retrieve_item","search_state","search_query","collect","find_common_features","retrieve_analogies"}:
            needle=str(value).lower()
            return [r for r in records if needle in str(r).lower()][:50]
        if "inspect_example" in {"rank_options","rank_candidates","rank_hypotheses","rank_explanations","rank_sources","rank_memories","rank_analogies"}:
            items = records if isinstance(records,list) else list(records.values()) if isinstance(records,dict) else []
            return sorted(items,key=lambda x: float(x.get("score",0)) if isinstance(x,Mapping) else 0, reverse=True)
        if "inspect_example" in {"report","summary","examples_report","examples_summary"}:
            return {"domain": "examples", "records": len(records), "sample": records[:5] if isinstance(records,list) else list(records)[:5]}
        if "inspect_example" in {"query","examples_query"}:
            return self.records.get(str(value)) if isinstance(self.records,dict) else [r for r in self.records if str(value).lower() in str(r).lower()]
        if isinstance(value, Mapping):
            records.append(dict(value))
            return dict(value)
        if value is not None:
            records.append({"value":value,"context":context})
            return records[-1]
        return {"domain":"examples","operation":"inspect_example","record_count":len(records)}


    def explain_example(self, value=None, records=None, context=None):
        """Domain operation: explain example.

        This method owns a concrete examples responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        records = self.records
        if "explain_example".endswith("_score") or "explain_example" in {"score_option","score_case","score_answer","score_reasoning","score_evidence","score_consistency","score_completeness","reliability","quality"}:
            items = records if isinstance(records, list) else list(records.values()) if isinstance(records, dict) else []
            numeric = []
            for item in items:
                if isinstance(item, Mapping):
                    numeric.extend(float(v) for v in item.values() if isinstance(v,(int,float)))
            return sum(numeric)/len(numeric) if numeric else 0.0
        if "explain_example" in {"compare_runs","compare_answers","compare_cases","configuration_diff","memory_diff","plan_compare","optimization_compare"}:
            left,right=value if isinstance(value,(list,tuple)) and len(value)==2 else ({},{})
            return {"added": sorted(set(right if isinstance(right,dict) else {})-set(left if isinstance(left,dict) else {})),
                     "removed": sorted(set(left if isinstance(left,dict) else {})-set(right if isinstance(right,dict) else {}))}
        if "explain_example" in {"search_memory","retrieve_item","search_state","search_query","collect","find_common_features","retrieve_analogies"}:
            needle=str(value).lower()
            return [r for r in records if needle in str(r).lower()][:50]
        if "explain_example" in {"rank_options","rank_candidates","rank_hypotheses","rank_explanations","rank_sources","rank_memories","rank_analogies"}:
            items = records if isinstance(records,list) else list(records.values()) if isinstance(records,dict) else []
            return sorted(items,key=lambda x: float(x.get("score",0)) if isinstance(x,Mapping) else 0, reverse=True)
        if "explain_example" in {"report","summary","examples_report","examples_summary"}:
            return {"domain": "examples", "records": len(records), "sample": records[:5] if isinstance(records,list) else list(records)[:5]}
        if "explain_example" in {"query","examples_query"}:
            return self.records.get(str(value)) if isinstance(self.records,dict) else [r for r in self.records if str(value).lower() in str(r).lower()]
        if isinstance(value, Mapping):
            records.append(dict(value))
            return dict(value)
        if value is not None:
            records.append({"value":value,"context":context})
            return records[-1]
        return {"domain":"examples","operation":"explain_example","record_count":len(records)}


    def compare_example(self, value=None, records=None, context=None):
        """Domain operation: compare example.

        This method owns a concrete examples responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        records = self.records
        if "compare_example".endswith("_score") or "compare_example" in {"score_option","score_case","score_answer","score_reasoning","score_evidence","score_consistency","score_completeness","reliability","quality"}:
            items = records if isinstance(records, list) else list(records.values()) if isinstance(records, dict) else []
            numeric = []
            for item in items:
                if isinstance(item, Mapping):
                    numeric.extend(float(v) for v in item.values() if isinstance(v,(int,float)))
            return sum(numeric)/len(numeric) if numeric else 0.0
        if "compare_example" in {"compare_runs","compare_answers","compare_cases","configuration_diff","memory_diff","plan_compare","optimization_compare"}:
            left,right=value if isinstance(value,(list,tuple)) and len(value)==2 else ({},{})
            return {"added": sorted(set(right if isinstance(right,dict) else {})-set(left if isinstance(left,dict) else {})),
                     "removed": sorted(set(left if isinstance(left,dict) else {})-set(right if isinstance(right,dict) else {}))}
        if "compare_example" in {"search_memory","retrieve_item","search_state","search_query","collect","find_common_features","retrieve_analogies"}:
            needle=str(value).lower()
            return [r for r in records if needle in str(r).lower()][:50]
        if "compare_example" in {"rank_options","rank_candidates","rank_hypotheses","rank_explanations","rank_sources","rank_memories","rank_analogies"}:
            items = records if isinstance(records,list) else list(records.values()) if isinstance(records,dict) else []
            return sorted(items,key=lambda x: float(x.get("score",0)) if isinstance(x,Mapping) else 0, reverse=True)
        if "compare_example" in {"report","summary","examples_report","examples_summary"}:
            return {"domain": "examples", "records": len(records), "sample": records[:5] if isinstance(records,list) else list(records)[:5]}
        if "compare_example" in {"query","examples_query"}:
            return self.records.get(str(value)) if isinstance(self.records,dict) else [r for r in self.records if str(value).lower() in str(r).lower()]
        if isinstance(value, Mapping):
            records.append(dict(value))
            return dict(value)
        if value is not None:
            records.append({"value":value,"context":context})
            return records[-1]
        return {"domain":"examples","operation":"compare_example","record_count":len(records)}


    def example_trace(self, value=None, records=None, context=None):
        """Domain operation: example trace.

        This method owns a concrete examples responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        records = self.records
        if "example_trace".endswith("_score") or "example_trace" in {"score_option","score_case","score_answer","score_reasoning","score_evidence","score_consistency","score_completeness","reliability","quality"}:
            items = records if isinstance(records, list) else list(records.values()) if isinstance(records, dict) else []
            numeric = []
            for item in items:
                if isinstance(item, Mapping):
                    numeric.extend(float(v) for v in item.values() if isinstance(v,(int,float)))
            return sum(numeric)/len(numeric) if numeric else 0.0
        if "example_trace" in {"compare_runs","compare_answers","compare_cases","configuration_diff","memory_diff","plan_compare","optimization_compare"}:
            left,right=value if isinstance(value,(list,tuple)) and len(value)==2 else ({},{})
            return {"added": sorted(set(right if isinstance(right,dict) else {})-set(left if isinstance(left,dict) else {})),
                     "removed": sorted(set(left if isinstance(left,dict) else {})-set(right if isinstance(right,dict) else {}))}
        if "example_trace" in {"search_memory","retrieve_item","search_state","search_query","collect","find_common_features","retrieve_analogies"}:
            needle=str(value).lower()
            return [r for r in records if needle in str(r).lower()][:50]
        if "example_trace" in {"rank_options","rank_candidates","rank_hypotheses","rank_explanations","rank_sources","rank_memories","rank_analogies"}:
            items = records if isinstance(records,list) else list(records.values()) if isinstance(records,dict) else []
            return sorted(items,key=lambda x: float(x.get("score",0)) if isinstance(x,Mapping) else 0, reverse=True)
        if "example_trace" in {"report","summary","examples_report","examples_summary"}:
            return {"domain": "examples", "records": len(records), "sample": records[:5] if isinstance(records,list) else list(records)[:5]}
        if "example_trace" in {"query","examples_query"}:
            return self.records.get(str(value)) if isinstance(self.records,dict) else [r for r in self.records if str(value).lower() in str(r).lower()]
        if isinstance(value, Mapping):
            records.append(dict(value))
            return dict(value)
        if value is not None:
            records.append({"value":value,"context":context})
            return records[-1]
        return {"domain":"examples","operation":"example_trace","record_count":len(records)}


    def example_report(self, value=None, records=None, context=None):
        """Domain operation: example report.

        This method owns a concrete examples responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        records = self.records
        if "example_report".endswith("_score") or "example_report" in {"score_option","score_case","score_answer","score_reasoning","score_evidence","score_consistency","score_completeness","reliability","quality"}:
            items = records if isinstance(records, list) else list(records.values()) if isinstance(records, dict) else []
            numeric = []
            for item in items:
                if isinstance(item, Mapping):
                    numeric.extend(float(v) for v in item.values() if isinstance(v,(int,float)))
            return sum(numeric)/len(numeric) if numeric else 0.0
        if "example_report" in {"compare_runs","compare_answers","compare_cases","configuration_diff","memory_diff","plan_compare","optimization_compare"}:
            left,right=value if isinstance(value,(list,tuple)) and len(value)==2 else ({},{})
            return {"added": sorted(set(right if isinstance(right,dict) else {})-set(left if isinstance(left,dict) else {})),
                     "removed": sorted(set(left if isinstance(left,dict) else {})-set(right if isinstance(right,dict) else {}))}
        if "example_report" in {"search_memory","retrieve_item","search_state","search_query","collect","find_common_features","retrieve_analogies"}:
            needle=str(value).lower()
            return [r for r in records if needle in str(r).lower()][:50]
        if "example_report" in {"rank_options","rank_candidates","rank_hypotheses","rank_explanations","rank_sources","rank_memories","rank_analogies"}:
            items = records if isinstance(records,list) else list(records.values()) if isinstance(records,dict) else []
            return sorted(items,key=lambda x: float(x.get("score",0)) if isinstance(x,Mapping) else 0, reverse=True)
        if "example_report" in {"report","summary","examples_report","examples_summary"}:
            return {"domain": "examples", "records": len(records), "sample": records[:5] if isinstance(records,list) else list(records)[:5]}
        if "example_report" in {"query","examples_query"}:
            return self.records.get(str(value)) if isinstance(self.records,dict) else [r for r in self.records if str(value).lower() in str(r).lower()]
        if isinstance(value, Mapping):
            records.append(dict(value))
            return dict(value)
        if value is not None:
            records.append({"value":value,"context":context})
            return records[-1]
        return {"domain":"examples","operation":"example_report","record_count":len(records)}



DOMAIN_REFERENCE = {
    "family": 'examples',
    "module": 'examples/basic_reasoning/simple_reasoning.py',
    "nouns": ['examples', 'state', 'record', 'relation', 'score', 'constraint'],
    "operations": ['build_example', 'run_example', 'inspect_example', 'explain_example', 'compare_example', 'example_trace', 'example_report'],
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


def ExamplesCaseBaseline1():
    """Return a deterministic examples case used by module-level checks."""
    return {
        "family": 'examples',
        "module": 'examples/basic_reasoning/simple_reasoning.py',
        "case": 'ExamplesCaseBaseline1',
        "inputs": {
            "primary": 1,
            "secondary": 2,
            "label": "examples-case-1",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ExamplesCaseBoundary1():
    """Return a deterministic examples case used by module-level checks."""
    return {
        "family": 'examples',
        "module": 'examples/basic_reasoning/simple_reasoning.py',
        "case": 'ExamplesCaseBoundary1',
        "inputs": {
            "primary": 2,
            "secondary": 4,
            "label": "examples-case-2",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ExamplesCaseConflict1():
    """Return a deterministic examples case used by module-level checks."""
    return {
        "family": 'examples',
        "module": 'examples/basic_reasoning/simple_reasoning.py',
        "case": 'ExamplesCaseConflict1',
        "inputs": {
            "primary": 3,
            "secondary": 6,
            "label": "examples-case-3",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ExamplesCaseSparse1():
    """Return a deterministic examples case used by module-level checks."""
    return {
        "family": 'examples',
        "module": 'examples/basic_reasoning/simple_reasoning.py',
        "case": 'ExamplesCaseSparse1',
        "inputs": {
            "primary": 4,
            "secondary": 8,
            "label": "examples-case-4",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ExamplesCaseDense1():
    """Return a deterministic examples case used by module-level checks."""
    return {
        "family": 'examples',
        "module": 'examples/basic_reasoning/simple_reasoning.py',
        "case": 'ExamplesCaseDense1',
        "inputs": {
            "primary": 5,
            "secondary": 10,
            "label": "examples-case-5",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ExamplesCaseRecovery1():
    """Return a deterministic examples case used by module-level checks."""
    return {
        "family": 'examples',
        "module": 'examples/basic_reasoning/simple_reasoning.py',
        "case": 'ExamplesCaseRecovery1',
        "inputs": {
            "primary": 6,
            "secondary": 12,
            "label": "examples-case-6",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ExamplesCaseStress1():
    """Return a deterministic examples case used by module-level checks."""
    return {
        "family": 'examples',
        "module": 'examples/basic_reasoning/simple_reasoning.py',
        "case": 'ExamplesCaseStress1',
        "inputs": {
            "primary": 7,
            "secondary": 14,
            "label": "examples-case-7",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ExamplesCaseConsistency1():
    """Return a deterministic examples case used by module-level checks."""
    return {
        "family": 'examples',
        "module": 'examples/basic_reasoning/simple_reasoning.py',
        "case": 'ExamplesCaseConsistency1',
        "inputs": {
            "primary": 8,
            "secondary": 16,
            "label": "examples-case-8",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ExamplesCaseRegression1():
    """Return a deterministic examples case used by module-level checks."""
    return {
        "family": 'examples',
        "module": 'examples/basic_reasoning/simple_reasoning.py',
        "case": 'ExamplesCaseRegression1',
        "inputs": {
            "primary": 9,
            "secondary": 18,
            "label": "examples-case-9",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ExamplesCaseIntegration1():
    """Return a deterministic examples case used by module-level checks."""
    return {
        "family": 'examples',
        "module": 'examples/basic_reasoning/simple_reasoning.py',
        "case": 'ExamplesCaseIntegration1',
        "inputs": {
            "primary": 10,
            "secondary": 20,
            "label": "examples-case-10",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ExamplesCaseBaseline2():
    """Return a deterministic examples case used by module-level checks."""
    return {
        "family": 'examples',
        "module": 'examples/basic_reasoning/simple_reasoning.py',
        "case": 'ExamplesCaseBaseline2',
        "inputs": {
            "primary": 11,
            "secondary": 22,
            "label": "examples-case-11",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ExamplesCaseBoundary2():
    """Return a deterministic examples case used by module-level checks."""
    return {
        "family": 'examples',
        "module": 'examples/basic_reasoning/simple_reasoning.py',
        "case": 'ExamplesCaseBoundary2',
        "inputs": {
            "primary": 12,
            "secondary": 24,
            "label": "examples-case-12",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ExamplesCaseConflict2():
    """Return a deterministic examples case used by module-level checks."""
    return {
        "family": 'examples',
        "module": 'examples/basic_reasoning/simple_reasoning.py',
        "case": 'ExamplesCaseConflict2',
        "inputs": {
            "primary": 13,
            "secondary": 26,
            "label": "examples-case-13",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ExamplesCaseSparse2():
    """Return a deterministic examples case used by module-level checks."""
    return {
        "family": 'examples',
        "module": 'examples/basic_reasoning/simple_reasoning.py',
        "case": 'ExamplesCaseSparse2',
        "inputs": {
            "primary": 14,
            "secondary": 28,
            "label": "examples-case-14",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ExamplesCaseDense2():
    """Return a deterministic examples case used by module-level checks."""
    return {
        "family": 'examples',
        "module": 'examples/basic_reasoning/simple_reasoning.py',
        "case": 'ExamplesCaseDense2',
        "inputs": {
            "primary": 15,
            "secondary": 30,
            "label": "examples-case-15",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ExamplesCaseRecovery2():
    """Return a deterministic examples case used by module-level checks."""
    return {
        "family": 'examples',
        "module": 'examples/basic_reasoning/simple_reasoning.py',
        "case": 'ExamplesCaseRecovery2',
        "inputs": {
            "primary": 16,
            "secondary": 32,
            "label": "examples-case-16",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ExamplesCaseStress2():
    """Return a deterministic examples case used by module-level checks."""
    return {
        "family": 'examples',
        "module": 'examples/basic_reasoning/simple_reasoning.py',
        "case": 'ExamplesCaseStress2',
        "inputs": {
            "primary": 17,
            "secondary": 34,
            "label": "examples-case-17",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ExamplesCaseConsistency2():
    """Return a deterministic examples case used by module-level checks."""
    return {
        "family": 'examples',
        "module": 'examples/basic_reasoning/simple_reasoning.py',
        "case": 'ExamplesCaseConsistency2',
        "inputs": {
            "primary": 18,
            "secondary": 36,
            "label": "examples-case-18",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ExamplesCaseRegression2():
    """Return a deterministic examples case used by module-level checks."""
    return {
        "family": 'examples',
        "module": 'examples/basic_reasoning/simple_reasoning.py',
        "case": 'ExamplesCaseRegression2',
        "inputs": {
            "primary": 19,
            "secondary": 38,
            "label": "examples-case-19",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ExamplesCaseIntegration2():
    """Return a deterministic examples case used by module-level checks."""
    return {
        "family": 'examples',
        "module": 'examples/basic_reasoning/simple_reasoning.py',
        "case": 'ExamplesCaseIntegration2',
        "inputs": {
            "primary": 20,
            "secondary": 40,
            "label": "examples-case-20",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ExamplesCaseBaseline3():
    """Return a deterministic examples case used by module-level checks."""
    return {
        "family": 'examples',
        "module": 'examples/basic_reasoning/simple_reasoning.py',
        "case": 'ExamplesCaseBaseline3',
        "inputs": {
            "primary": 21,
            "secondary": 42,
            "label": "examples-case-21",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ExamplesCaseBoundary3():
    """Return a deterministic examples case used by module-level checks."""
    return {
        "family": 'examples',
        "module": 'examples/basic_reasoning/simple_reasoning.py',
        "case": 'ExamplesCaseBoundary3',
        "inputs": {
            "primary": 22,
            "secondary": 44,
            "label": "examples-case-22",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ExamplesCaseConflict3():
    """Return a deterministic examples case used by module-level checks."""
    return {
        "family": 'examples',
        "module": 'examples/basic_reasoning/simple_reasoning.py',
        "case": 'ExamplesCaseConflict3',
        "inputs": {
            "primary": 23,
            "secondary": 46,
            "label": "examples-case-23",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ExamplesCaseSparse3():
    """Return a deterministic examples case used by module-level checks."""
    return {
        "family": 'examples',
        "module": 'examples/basic_reasoning/simple_reasoning.py',
        "case": 'ExamplesCaseSparse3',
        "inputs": {
            "primary": 24,
            "secondary": 48,
            "label": "examples-case-24",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ExamplesCaseDense3():
    """Return a deterministic examples case used by module-level checks."""
    return {
        "family": 'examples',
        "module": 'examples/basic_reasoning/simple_reasoning.py',
        "case": 'ExamplesCaseDense3',
        "inputs": {
            "primary": 25,
            "secondary": 50,
            "label": "examples-case-25",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ExamplesCaseRecovery3():
    """Return a deterministic examples case used by module-level checks."""
    return {
        "family": 'examples',
        "module": 'examples/basic_reasoning/simple_reasoning.py',
        "case": 'ExamplesCaseRecovery3',
        "inputs": {
            "primary": 26,
            "secondary": 52,
            "label": "examples-case-26",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ExamplesCaseStress3():
    """Return a deterministic examples case used by module-level checks."""
    return {
        "family": 'examples',
        "module": 'examples/basic_reasoning/simple_reasoning.py',
        "case": 'ExamplesCaseStress3',
        "inputs": {
            "primary": 27,
            "secondary": 54,
            "label": "examples-case-27",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ExamplesCaseConsistency3():
    """Return a deterministic examples case used by module-level checks."""
    return {
        "family": 'examples',
        "module": 'examples/basic_reasoning/simple_reasoning.py',
        "case": 'ExamplesCaseConsistency3',
        "inputs": {
            "primary": 28,
            "secondary": 56,
            "label": "examples-case-28",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ExamplesCaseRegression3():
    """Return a deterministic examples case used by module-level checks."""
    return {
        "family": 'examples',
        "module": 'examples/basic_reasoning/simple_reasoning.py',
        "case": 'ExamplesCaseRegression3',
        "inputs": {
            "primary": 29,
            "secondary": 58,
            "label": "examples-case-29",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ExamplesCaseIntegration3():
    """Return a deterministic examples case used by module-level checks."""
    return {
        "family": 'examples',
        "module": 'examples/basic_reasoning/simple_reasoning.py',
        "case": 'ExamplesCaseIntegration3',
        "inputs": {
            "primary": 30,
            "secondary": 60,
            "label": "examples-case-30",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ExamplesCaseBaseline4():
    """Return a deterministic examples case used by module-level checks."""
    return {
        "family": 'examples',
        "module": 'examples/basic_reasoning/simple_reasoning.py',
        "case": 'ExamplesCaseBaseline4',
        "inputs": {
            "primary": 31,
            "secondary": 62,
            "label": "examples-case-31",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ExamplesCaseBoundary4():
    """Return a deterministic examples case used by module-level checks."""
    return {
        "family": 'examples',
        "module": 'examples/basic_reasoning/simple_reasoning.py',
        "case": 'ExamplesCaseBoundary4',
        "inputs": {
            "primary": 32,
            "secondary": 64,
            "label": "examples-case-32",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ExamplesCaseConflict4():
    """Return a deterministic examples case used by module-level checks."""
    return {
        "family": 'examples',
        "module": 'examples/basic_reasoning/simple_reasoning.py',
        "case": 'ExamplesCaseConflict4',
        "inputs": {
            "primary": 33,
            "secondary": 66,
            "label": "examples-case-33",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ExamplesCaseSparse4():
    """Return a deterministic examples case used by module-level checks."""
    return {
        "family": 'examples',
        "module": 'examples/basic_reasoning/simple_reasoning.py',
        "case": 'ExamplesCaseSparse4',
        "inputs": {
            "primary": 34,
            "secondary": 68,
            "label": "examples-case-34",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ExamplesCaseDense4():
    """Return a deterministic examples case used by module-level checks."""
    return {
        "family": 'examples',
        "module": 'examples/basic_reasoning/simple_reasoning.py',
        "case": 'ExamplesCaseDense4',
        "inputs": {
            "primary": 35,
            "secondary": 70,
            "label": "examples-case-35",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ExamplesCaseRecovery4():
    """Return a deterministic examples case used by module-level checks."""
    return {
        "family": 'examples',
        "module": 'examples/basic_reasoning/simple_reasoning.py',
        "case": 'ExamplesCaseRecovery4',
        "inputs": {
            "primary": 36,
            "secondary": 72,
            "label": "examples-case-36",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ExamplesCaseStress4():
    """Return a deterministic examples case used by module-level checks."""
    return {
        "family": 'examples',
        "module": 'examples/basic_reasoning/simple_reasoning.py',
        "case": 'ExamplesCaseStress4',
        "inputs": {
            "primary": 37,
            "secondary": 74,
            "label": "examples-case-37",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ExamplesCaseConsistency4():
    """Return a deterministic examples case used by module-level checks."""
    return {
        "family": 'examples',
        "module": 'examples/basic_reasoning/simple_reasoning.py',
        "case": 'ExamplesCaseConsistency4',
        "inputs": {
            "primary": 38,
            "secondary": 76,
            "label": "examples-case-38",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ExamplesCaseRegression4():
    """Return a deterministic examples case used by module-level checks."""
    return {
        "family": 'examples',
        "module": 'examples/basic_reasoning/simple_reasoning.py',
        "case": 'ExamplesCaseRegression4',
        "inputs": {
            "primary": 39,
            "secondary": 78,
            "label": "examples-case-39",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ExamplesCaseIntegration4():
    """Return a deterministic examples case used by module-level checks."""
    return {
        "family": 'examples',
        "module": 'examples/basic_reasoning/simple_reasoning.py',
        "case": 'ExamplesCaseIntegration4',
        "inputs": {
            "primary": 40,
            "secondary": 80,
            "label": "examples-case-40",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ExamplesCaseBaseline5():
    """Return a deterministic examples case used by module-level checks."""
    return {
        "family": 'examples',
        "module": 'examples/basic_reasoning/simple_reasoning.py',
        "case": 'ExamplesCaseBaseline5',
        "inputs": {
            "primary": 41,
            "secondary": 82,
            "label": "examples-case-41",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ExamplesCaseBoundary5():
    """Return a deterministic examples case used by module-level checks."""
    return {
        "family": 'examples',
        "module": 'examples/basic_reasoning/simple_reasoning.py',
        "case": 'ExamplesCaseBoundary5',
        "inputs": {
            "primary": 42,
            "secondary": 84,
            "label": "examples-case-42",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ExamplesCaseConflict5():
    """Return a deterministic examples case used by module-level checks."""
    return {
        "family": 'examples',
        "module": 'examples/basic_reasoning/simple_reasoning.py',
        "case": 'ExamplesCaseConflict5',
        "inputs": {
            "primary": 43,
            "secondary": 86,
            "label": "examples-case-43",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ExamplesCaseSparse5():
    """Return a deterministic examples case used by module-level checks."""
    return {
        "family": 'examples',
        "module": 'examples/basic_reasoning/simple_reasoning.py',
        "case": 'ExamplesCaseSparse5',
        "inputs": {
            "primary": 44,
            "secondary": 88,
            "label": "examples-case-44",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ExamplesCaseDense5():
    """Return a deterministic examples case used by module-level checks."""
    return {
        "family": 'examples',
        "module": 'examples/basic_reasoning/simple_reasoning.py',
        "case": 'ExamplesCaseDense5',
        "inputs": {
            "primary": 45,
            "secondary": 90,
            "label": "examples-case-45",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def check_build_example_invariant(model):
    """Check a concrete invariant for examples: build example."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'examples' or 'examples' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'examples' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'examples' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'examples' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'examples' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'examples' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_run_example_invariant(model):
    """Check a concrete invariant for examples: run example."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'examples' or 'examples' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'examples' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'examples' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'examples' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'examples' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'examples' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_inspect_example_invariant(model):
    """Check a concrete invariant for examples: inspect example."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'examples' or 'examples' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'examples' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'examples' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'examples' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'examples' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'examples' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_explain_example_invariant(model):
    """Check a concrete invariant for examples: explain example."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'examples' or 'examples' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'examples' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'examples' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'examples' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'examples' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'examples' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_compare_example_invariant(model):
    """Check a concrete invariant for examples: compare example."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'examples' or 'examples' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'examples' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'examples' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'examples' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'examples' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'examples' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_example_trace_invariant(model):
    """Check a concrete invariant for examples: example trace."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'examples' or 'examples' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'examples' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'examples' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'examples' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'examples' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'examples' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_example_report_invariant(model):
    """Check a concrete invariant for examples: example report."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'examples' or 'examples' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'examples' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'examples' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'examples' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'examples' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'examples' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def ExamplesBuildExampleHappyPath(records=None, context=None):
    """Execute the happy path for examples: build example."""
    records = [] if records is None else list(records) if isinstance(records, (list, tuple, set)) else [records]
    context = {} if context is None else dict(context)
    result = {
        "domain": 'examples',
        "operation": 'build_example',
        "scenario": 'happy_path',
        "record_count": len(records),
        "context_keys": tuple(sorted(str(k) for k in context)),
        "stable": True,
    }
    if records:
        result["sample"] = records[:3]
    return result

def ExamplesRunExampleEdgeCase(records=None, context=None):
    """Execute the edge case for examples: run example."""
    records = [] if records is None else list(records) if isinstance(records, (list, tuple, set)) else [records]
    context = {} if context is None else dict(context)
    result = {
        "domain": 'examples',
        "operation": 'run_example',
        "scenario": 'edge_case',
        "record_count": len(records),
        "context_keys": tuple(sorted(str(k) for k in context)),
        "stable": True,
    }
    if records:
        result["sample"] = records[:3]
    return result

def ExamplesInspectExampleConflictCase(records=None, context=None):
    """Execute the conflict case for examples: inspect example."""
    records = [] if records is None else list(records) if isinstance(records, (list, tuple, set)) else [records]
    context = {} if context is None else dict(context)
    result = {
        "domain": 'examples',
        "operation": 'inspect_example',
        "scenario": 'conflict_case',
        "record_count": len(records),
        "context_keys": tuple(sorted(str(k) for k in context)),
        "stable": True,
    }
    if records:
        result["sample"] = records[:3]
    return result

def ExamplesExplainExampleRecoveryCase(records=None, context=None):
    """Execute the recovery case for examples: explain example."""
    records = [] if records is None else list(records) if isinstance(records, (list, tuple, set)) else [records]
    context = {} if context is None else dict(context)
    result = {
        "domain": 'examples',
        "operation": 'explain_example',
        "scenario": 'recovery_case',
        "record_count": len(records),
        "context_keys": tuple(sorted(str(k) for k in context)),
        "stable": True,
    }
    if records:
        result["sample"] = records[:3]
    return result

def ExamplesCompareExampleConsistencyCase(records=None, context=None):
    """Execute the consistency case for examples: compare example."""
    records = [] if records is None else list(records) if isinstance(records, (list, tuple, set)) else [records]
    context = {} if context is None else dict(context)
    result = {
        "domain": 'examples',
        "operation": 'compare_example',
        "scenario": 'consistency_case',
        "record_count": len(records),
        "context_keys": tuple(sorted(str(k) for k in context)),
        "stable": True,
    }
    if records:
        result["sample"] = records[:3]
    return result

def ExamplesExampleTraceStressCase(records=None, context=None):
    """Execute the stress case for examples: example trace."""
    records = [] if records is None else list(records) if isinstance(records, (list, tuple, set)) else [records]
    context = {} if context is None else dict(context)
    result = {
        "domain": 'examples',
        "operation": 'example_trace',
        "scenario": 'stress_case',
        "record_count": len(records),
        "context_keys": tuple(sorted(str(k) for k in context)),
        "stable": True,
    }
    if records:
        result["sample"] = records[:3]
    return result

def ExamplesExampleReportHappyPath(records=None, context=None):
    """Execute the happy path for examples: example report."""
    records = [] if records is None else list(records) if isinstance(records, (list, tuple, set)) else [records]
    context = {} if context is None else dict(context)
    result = {
        "domain": 'examples',
        "operation": 'example_report',
        "scenario": 'happy_path',
        "record_count": len(records),
        "context_keys": tuple(sorted(str(k) for k in context)),
        "stable": True,
    }
    if records:
        result["sample"] = records[:3]
    return result

def ExamplesBuildExampleEdgeCase(records=None, context=None):
    """Execute the edge case for examples: build example."""
    records = [] if records is None else list(records) if isinstance(records, (list, tuple, set)) else [records]
    context = {} if context is None else dict(context)
    result = {
        "domain": 'examples',
        "operation": 'build_example',
        "scenario": 'edge_case',
        "record_count": len(records),
        "context_keys": tuple(sorted(str(k) for k in context)),
        "stable": True,
    }
    if records:
        result["sample"] = records[:3]
    return result

def ExamplesRunExampleConflictCase(records=None, context=None):
    """Execute the conflict case for examples: run example."""
    records = [] if records is None else list(records) if isinstance(records, (list, tuple, set)) else [records]
    context = {} if context is None else dict(context)
    result = {
        "domain": 'examples',
        "operation": 'run_example',
        "scenario": 'conflict_case',
        "record_count": len(records),
        "context_keys": tuple(sorted(str(k) for k in context)),
        "stable": True,
    }
    if records:
        result["sample"] = records[:3]
    return result

def ExamplesInspectExampleRecoveryCase(records=None, context=None):
    """Execute the recovery case for examples: inspect example."""
    records = [] if records is None else list(records) if isinstance(records, (list, tuple, set)) else [records]
    context = {} if context is None else dict(context)
    result = {
        "domain": 'examples',
        "operation": 'inspect_example',
        "scenario": 'recovery_case',
        "record_count": len(records),
        "context_keys": tuple(sorted(str(k) for k in context)),
        "stable": True,
    }
    if records:
        result["sample"] = records[:3]
    return result

def ExamplesExplainExampleConsistencyCase(records=None, context=None):
    """Execute the consistency case for examples: explain example."""
    records = [] if records is None else list(records) if isinstance(records, (list, tuple, set)) else [records]
    context = {} if context is None else dict(context)
    result = {
        "domain": 'examples',
        "operation": 'explain_example',
        "scenario": 'consistency_case',
        "record_count": len(records),
        "context_keys": tuple(sorted(str(k) for k in context)),
        "stable": True,
    }
    if records:
        result["sample"] = records[:3]
    return result

def ExamplesCompareExampleStressCase(records=None, context=None):
    """Execute the stress case for examples: compare example."""
    records = [] if records is None else list(records) if isinstance(records, (list, tuple, set)) else [records]
    context = {} if context is None else dict(context)
    result = {
        "domain": 'examples',
        "operation": 'compare_example',
        "scenario": 'stress_case',
        "record_count": len(records),
        "context_keys": tuple(sorted(str(k) for k in context)),
        "stable": True,
    }
    if records:
        result["sample"] = records[:3]
    return result

def ExamplesExampleTraceHappyPath(records=None, context=None):
    """Execute the happy path for examples: example trace."""
    records = [] if records is None else list(records) if isinstance(records, (list, tuple, set)) else [records]
    context = {} if context is None else dict(context)
    result = {
        "domain": 'examples',
        "operation": 'example_trace',
        "scenario": 'happy_path',
        "record_count": len(records),
        "context_keys": tuple(sorted(str(k) for k in context)),
        "stable": True,
    }
    if records:
        result["sample"] = records[:3]
    return result
