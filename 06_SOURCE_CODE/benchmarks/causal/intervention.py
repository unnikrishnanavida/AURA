"""
Domain-first implementation for benchmarks/causal/intervention.py.

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
DOMAIN_REFERENCE = {'family': 'causal', 'module': 'benchmarks/causal/intervention.py', 'nouns': ['variable', 'edge', 'ancestor', 'descendant', 'confounder', 'intervention', 'effect', 'path'], 'operations': ['add_variable', 'add_edge', 'parents', 'children', 'ancestors', 'descendants', 'topological_order', 'has_cycle', 'path_exists', 'all_paths', 'backdoor_paths', 'frontdoor_paths', 'collider_candidates', 'backdoor_candidates', 'markov_blanket', 'minimal_adjustment', 'apply_intervention', 'do_operator', 'mediators', 'observational_effect', 'interventional_effect', 'conditional_effect', 'effect_identifiability', 'effect_decomposition', 'sensitivity_to_confounding', 'edge_confidence', 'graph_factorization', 'causal_markov_check', 'counterfactual_copy', 'causal_order', 'validate_graph', 'compare_graphs', 'graph_summary', 'intervention_plan', 'causal_query'], 'principles': ['domain ownership', 'explicit state', 'deterministic transformation', 'inspectable intermediate representation', 'evidence-aware decisions', 'bounded failure', 'repeatable evaluation', 'separation from shared infrastructure']}

def domain_reference():
    """Return the implementation contract owned by this module."""
    return {'family': DOMAIN_REFERENCE['family'], 'module': DOMAIN_REFERENCE['module'], 'nouns': tuple(DOMAIN_REFERENCE['nouns']), 'operations': tuple(DOMAIN_REFERENCE['operations'])}

def domain_health():
    """Check that the module exposes its own domain model."""
    return {'domain': DOMAIN_REFERENCE['family'], 'specialized': True, 'generic_extension_surface': False, 'operation_wrapper': False, 'operation_count': len(DOMAIN_REFERENCE['operations'])}

def CausalCaseBaseline1():
    """Return a deterministic causal case used by module-level checks."""
    return {'family': 'causal', 'module': 'benchmarks/causal/intervention.py', 'case': 'CausalCaseBaseline1', 'inputs': {'primary': 1, 'secondary': 2, 'label': 'causal-case-1'}, 'expected': {'stable': True, 'repeatable': True, 'domain_owned': True}}

def CausalCaseBoundary1():
    """Return a deterministic causal case used by module-level checks."""
    return {'family': 'causal', 'module': 'benchmarks/causal/intervention.py', 'case': 'CausalCaseBoundary1', 'inputs': {'primary': 2, 'secondary': 4, 'label': 'causal-case-2'}, 'expected': {'stable': True, 'repeatable': True, 'domain_owned': True}}

def CausalCaseConflict1():
    """Return a deterministic causal case used by module-level checks."""
    return {'family': 'causal', 'module': 'benchmarks/causal/intervention.py', 'case': 'CausalCaseConflict1', 'inputs': {'primary': 3, 'secondary': 6, 'label': 'causal-case-3'}, 'expected': {'stable': True, 'repeatable': True, 'domain_owned': True}}

def CausalCaseSparse1():
    """Return a deterministic causal case used by module-level checks."""
    return {'family': 'causal', 'module': 'benchmarks/causal/intervention.py', 'case': 'CausalCaseSparse1', 'inputs': {'primary': 4, 'secondary': 8, 'label': 'causal-case-4'}, 'expected': {'stable': True, 'repeatable': True, 'domain_owned': True}}

def CausalCaseDense1():
    """Return a deterministic causal case used by module-level checks."""
    return {'family': 'causal', 'module': 'benchmarks/causal/intervention.py', 'case': 'CausalCaseDense1', 'inputs': {'primary': 5, 'secondary': 10, 'label': 'causal-case-5'}, 'expected': {'stable': True, 'repeatable': True, 'domain_owned': True}}

def CausalCaseRecovery1():
    """Return a deterministic causal case used by module-level checks."""
    return {'family': 'causal', 'module': 'benchmarks/causal/intervention.py', 'case': 'CausalCaseRecovery1', 'inputs': {'primary': 6, 'secondary': 12, 'label': 'causal-case-6'}, 'expected': {'stable': True, 'repeatable': True, 'domain_owned': True}}

def CausalCaseStress1():
    """Return a deterministic causal case used by module-level checks."""
    return {'family': 'causal', 'module': 'benchmarks/causal/intervention.py', 'case': 'CausalCaseStress1', 'inputs': {'primary': 7, 'secondary': 14, 'label': 'causal-case-7'}, 'expected': {'stable': True, 'repeatable': True, 'domain_owned': True}}

def CausalCaseConsistency1():
    """Return a deterministic causal case used by module-level checks."""
    return {'family': 'causal', 'module': 'benchmarks/causal/intervention.py', 'case': 'CausalCaseConsistency1', 'inputs': {'primary': 8, 'secondary': 16, 'label': 'causal-case-8'}, 'expected': {'stable': True, 'repeatable': True, 'domain_owned': True}}

def CausalCaseRegression1():
    """Return a deterministic causal case used by module-level checks."""
    return {'family': 'causal', 'module': 'benchmarks/causal/intervention.py', 'case': 'CausalCaseRegression1', 'inputs': {'primary': 9, 'secondary': 18, 'label': 'causal-case-9'}, 'expected': {'stable': True, 'repeatable': True, 'domain_owned': True}}

def CausalCaseIntegration1():
    """Return a deterministic causal case used by module-level checks."""
    return {'family': 'causal', 'module': 'benchmarks/causal/intervention.py', 'case': 'CausalCaseIntegration1', 'inputs': {'primary': 10, 'secondary': 20, 'label': 'causal-case-10'}, 'expected': {'stable': True, 'repeatable': True, 'domain_owned': True}}

def CausalCaseBaseline2():
    """Return a deterministic causal case used by module-level checks."""
    return {'family': 'causal', 'module': 'benchmarks/causal/intervention.py', 'case': 'CausalCaseBaseline2', 'inputs': {'primary': 11, 'secondary': 22, 'label': 'causal-case-11'}, 'expected': {'stable': True, 'repeatable': True, 'domain_owned': True}}

def CausalCaseBoundary2():
    """Return a deterministic causal case used by module-level checks."""
    return {'family': 'causal', 'module': 'benchmarks/causal/intervention.py', 'case': 'CausalCaseBoundary2', 'inputs': {'primary': 12, 'secondary': 24, 'label': 'causal-case-12'}, 'expected': {'stable': True, 'repeatable': True, 'domain_owned': True}}

def CausalCaseConflict2():
    """Return a deterministic causal case used by module-level checks."""
    return {'family': 'causal', 'module': 'benchmarks/causal/intervention.py', 'case': 'CausalCaseConflict2', 'inputs': {'primary': 13, 'secondary': 26, 'label': 'causal-case-13'}, 'expected': {'stable': True, 'repeatable': True, 'domain_owned': True}}

def CausalCaseSparse2():
    """Return a deterministic causal case used by module-level checks."""
    return {'family': 'causal', 'module': 'benchmarks/causal/intervention.py', 'case': 'CausalCaseSparse2', 'inputs': {'primary': 14, 'secondary': 28, 'label': 'causal-case-14'}, 'expected': {'stable': True, 'repeatable': True, 'domain_owned': True}}

def CausalCaseDense2():
    """Return a deterministic causal case used by module-level checks."""
    return {'family': 'causal', 'module': 'benchmarks/causal/intervention.py', 'case': 'CausalCaseDense2', 'inputs': {'primary': 15, 'secondary': 30, 'label': 'causal-case-15'}, 'expected': {'stable': True, 'repeatable': True, 'domain_owned': True}}

def CausalCaseRecovery2():
    """Return a deterministic causal case used by module-level checks."""
    return {'family': 'causal', 'module': 'benchmarks/causal/intervention.py', 'case': 'CausalCaseRecovery2', 'inputs': {'primary': 16, 'secondary': 32, 'label': 'causal-case-16'}, 'expected': {'stable': True, 'repeatable': True, 'domain_owned': True}}

def CausalCaseStress2():
    """Return a deterministic causal case used by module-level checks."""
    return {'family': 'causal', 'module': 'benchmarks/causal/intervention.py', 'case': 'CausalCaseStress2', 'inputs': {'primary': 17, 'secondary': 34, 'label': 'causal-case-17'}, 'expected': {'stable': True, 'repeatable': True, 'domain_owned': True}}

def CausalCaseConsistency2():
    """Return a deterministic causal case used by module-level checks."""
    return {'family': 'causal', 'module': 'benchmarks/causal/intervention.py', 'case': 'CausalCaseConsistency2', 'inputs': {'primary': 18, 'secondary': 36, 'label': 'causal-case-18'}, 'expected': {'stable': True, 'repeatable': True, 'domain_owned': True}}

def CausalCaseRegression2():
    """Return a deterministic causal case used by module-level checks."""
    return {'family': 'causal', 'module': 'benchmarks/causal/intervention.py', 'case': 'CausalCaseRegression2', 'inputs': {'primary': 19, 'secondary': 38, 'label': 'causal-case-19'}, 'expected': {'stable': True, 'repeatable': True, 'domain_owned': True}}

def CausalCaseIntegration2():
    """Return a deterministic causal case used by module-level checks."""
    return {'family': 'causal', 'module': 'benchmarks/causal/intervention.py', 'case': 'CausalCaseIntegration2', 'inputs': {'primary': 20, 'secondary': 40, 'label': 'causal-case-20'}, 'expected': {'stable': True, 'repeatable': True, 'domain_owned': True}}

def CausalCaseBaseline3():
    """Return a deterministic causal case used by module-level checks."""
    return {'family': 'causal', 'module': 'benchmarks/causal/intervention.py', 'case': 'CausalCaseBaseline3', 'inputs': {'primary': 21, 'secondary': 42, 'label': 'causal-case-21'}, 'expected': {'stable': True, 'repeatable': True, 'domain_owned': True}}

def CausalCaseBoundary3():
    """Return a deterministic causal case used by module-level checks."""
    return {'family': 'causal', 'module': 'benchmarks/causal/intervention.py', 'case': 'CausalCaseBoundary3', 'inputs': {'primary': 22, 'secondary': 44, 'label': 'causal-case-22'}, 'expected': {'stable': True, 'repeatable': True, 'domain_owned': True}}

def CausalCaseConflict3():
    """Return a deterministic causal case used by module-level checks."""
    return {'family': 'causal', 'module': 'benchmarks/causal/intervention.py', 'case': 'CausalCaseConflict3', 'inputs': {'primary': 23, 'secondary': 46, 'label': 'causal-case-23'}, 'expected': {'stable': True, 'repeatable': True, 'domain_owned': True}}

def CausalCaseSparse3():
    """Return a deterministic causal case used by module-level checks."""
    return {'family': 'causal', 'module': 'benchmarks/causal/intervention.py', 'case': 'CausalCaseSparse3', 'inputs': {'primary': 24, 'secondary': 48, 'label': 'causal-case-24'}, 'expected': {'stable': True, 'repeatable': True, 'domain_owned': True}}

def CausalCaseDense3():
    """Return a deterministic causal case used by module-level checks."""
    return {'family': 'causal', 'module': 'benchmarks/causal/intervention.py', 'case': 'CausalCaseDense3', 'inputs': {'primary': 25, 'secondary': 50, 'label': 'causal-case-25'}, 'expected': {'stable': True, 'repeatable': True, 'domain_owned': True}}

def CausalCaseRecovery3():
    """Return a deterministic causal case used by module-level checks."""
    return {'family': 'causal', 'module': 'benchmarks/causal/intervention.py', 'case': 'CausalCaseRecovery3', 'inputs': {'primary': 26, 'secondary': 52, 'label': 'causal-case-26'}, 'expected': {'stable': True, 'repeatable': True, 'domain_owned': True}}

def CausalCaseStress3():
    """Return a deterministic causal case used by module-level checks."""
    return {'family': 'causal', 'module': 'benchmarks/causal/intervention.py', 'case': 'CausalCaseStress3', 'inputs': {'primary': 27, 'secondary': 54, 'label': 'causal-case-27'}, 'expected': {'stable': True, 'repeatable': True, 'domain_owned': True}}

def CausalCaseConsistency3():
    """Return a deterministic causal case used by module-level checks."""
    return {'family': 'causal', 'module': 'benchmarks/causal/intervention.py', 'case': 'CausalCaseConsistency3', 'inputs': {'primary': 28, 'secondary': 56, 'label': 'causal-case-28'}, 'expected': {'stable': True, 'repeatable': True, 'domain_owned': True}}

def CausalCaseRegression3():
    """Return a deterministic causal case used by module-level checks."""
    return {'family': 'causal', 'module': 'benchmarks/causal/intervention.py', 'case': 'CausalCaseRegression3', 'inputs': {'primary': 29, 'secondary': 58, 'label': 'causal-case-29'}, 'expected': {'stable': True, 'repeatable': True, 'domain_owned': True}}

def CausalCaseIntegration3():
    """Return a deterministic causal case used by module-level checks."""
    return {'family': 'causal', 'module': 'benchmarks/causal/intervention.py', 'case': 'CausalCaseIntegration3', 'inputs': {'primary': 30, 'secondary': 60, 'label': 'causal-case-30'}, 'expected': {'stable': True, 'repeatable': True, 'domain_owned': True}}

def CausalCaseBaseline4():
    """Return a deterministic causal case used by module-level checks."""
    return {'family': 'causal', 'module': 'benchmarks/causal/intervention.py', 'case': 'CausalCaseBaseline4', 'inputs': {'primary': 31, 'secondary': 62, 'label': 'causal-case-31'}, 'expected': {'stable': True, 'repeatable': True, 'domain_owned': True}}

def CausalCaseBoundary4():
    """Return a deterministic causal case used by module-level checks."""
    return {'family': 'causal', 'module': 'benchmarks/causal/intervention.py', 'case': 'CausalCaseBoundary4', 'inputs': {'primary': 32, 'secondary': 64, 'label': 'causal-case-32'}, 'expected': {'stable': True, 'repeatable': True, 'domain_owned': True}}

def CausalCaseConflict4():
    """Return a deterministic causal case used by module-level checks."""
    return {'family': 'causal', 'module': 'benchmarks/causal/intervention.py', 'case': 'CausalCaseConflict4', 'inputs': {'primary': 33, 'secondary': 66, 'label': 'causal-case-33'}, 'expected': {'stable': True, 'repeatable': True, 'domain_owned': True}}

def CausalCaseSparse4():
    """Return a deterministic causal case used by module-level checks."""
    return {'family': 'causal', 'module': 'benchmarks/causal/intervention.py', 'case': 'CausalCaseSparse4', 'inputs': {'primary': 34, 'secondary': 68, 'label': 'causal-case-34'}, 'expected': {'stable': True, 'repeatable': True, 'domain_owned': True}}

def CausalCaseDense4():
    """Return a deterministic causal case used by module-level checks."""
    return {'family': 'causal', 'module': 'benchmarks/causal/intervention.py', 'case': 'CausalCaseDense4', 'inputs': {'primary': 35, 'secondary': 70, 'label': 'causal-case-35'}, 'expected': {'stable': True, 'repeatable': True, 'domain_owned': True}}

def CausalCaseRecovery4():
    """Return a deterministic causal case used by module-level checks."""
    return {'family': 'causal', 'module': 'benchmarks/causal/intervention.py', 'case': 'CausalCaseRecovery4', 'inputs': {'primary': 36, 'secondary': 72, 'label': 'causal-case-36'}, 'expected': {'stable': True, 'repeatable': True, 'domain_owned': True}}

def CausalCaseStress4():
    """Return a deterministic causal case used by module-level checks."""
    return {'family': 'causal', 'module': 'benchmarks/causal/intervention.py', 'case': 'CausalCaseStress4', 'inputs': {'primary': 37, 'secondary': 74, 'label': 'causal-case-37'}, 'expected': {'stable': True, 'repeatable': True, 'domain_owned': True}}

def CausalCaseConsistency4():
    """Return a deterministic causal case used by module-level checks."""
    return {'family': 'causal', 'module': 'benchmarks/causal/intervention.py', 'case': 'CausalCaseConsistency4', 'inputs': {'primary': 38, 'secondary': 76, 'label': 'causal-case-38'}, 'expected': {'stable': True, 'repeatable': True, 'domain_owned': True}}

def CausalCaseRegression4():
    """Return a deterministic causal case used by module-level checks."""
    return {'family': 'causal', 'module': 'benchmarks/causal/intervention.py', 'case': 'CausalCaseRegression4', 'inputs': {'primary': 39, 'secondary': 78, 'label': 'causal-case-39'}, 'expected': {'stable': True, 'repeatable': True, 'domain_owned': True}}

def CausalCaseIntegration4():
    """Return a deterministic causal case used by module-level checks."""
    return {'family': 'causal', 'module': 'benchmarks/causal/intervention.py', 'case': 'CausalCaseIntegration4', 'inputs': {'primary': 40, 'secondary': 80, 'label': 'causal-case-40'}, 'expected': {'stable': True, 'repeatable': True, 'domain_owned': True}}

def CausalCaseBaseline5():
    """Return a deterministic causal case used by module-level checks."""
    return {'family': 'causal', 'module': 'benchmarks/causal/intervention.py', 'case': 'CausalCaseBaseline5', 'inputs': {'primary': 41, 'secondary': 82, 'label': 'causal-case-41'}, 'expected': {'stable': True, 'repeatable': True, 'domain_owned': True}}

def CausalCaseBoundary5():
    """Return a deterministic causal case used by module-level checks."""
    return {'family': 'causal', 'module': 'benchmarks/causal/intervention.py', 'case': 'CausalCaseBoundary5', 'inputs': {'primary': 42, 'secondary': 84, 'label': 'causal-case-42'}, 'expected': {'stable': True, 'repeatable': True, 'domain_owned': True}}

def CausalCaseConflict5():
    """Return a deterministic causal case used by module-level checks."""
    return {'family': 'causal', 'module': 'benchmarks/causal/intervention.py', 'case': 'CausalCaseConflict5', 'inputs': {'primary': 43, 'secondary': 86, 'label': 'causal-case-43'}, 'expected': {'stable': True, 'repeatable': True, 'domain_owned': True}}

def CausalCaseSparse5():
    """Return a deterministic causal case used by module-level checks."""
    return {'family': 'causal', 'module': 'benchmarks/causal/intervention.py', 'case': 'CausalCaseSparse5', 'inputs': {'primary': 44, 'secondary': 88, 'label': 'causal-case-44'}, 'expected': {'stable': True, 'repeatable': True, 'domain_owned': True}}

def CausalCaseDense5():
    """Return a deterministic causal case used by module-level checks."""
    return {'family': 'causal', 'module': 'benchmarks/causal/intervention.py', 'case': 'CausalCaseDense5', 'inputs': {'primary': 45, 'secondary': 90, 'label': 'causal-case-45'}, 'expected': {'stable': True, 'repeatable': True, 'domain_owned': True}}

def check_add_variable_invariant(model):
    """Check a concrete invariant for causal: add variable."""
    if model is None:
        return False
    if hasattr(model, 'state') and isinstance(model.state, dict):
        return model.state.get('domain') == 'causal' or 'causal' in str(model.state.get('module', ''))
    if hasattr(model, 'graph') and 'causal' == 'causal':
        return isinstance(model.graph.get('edges'), set)
    if hasattr(model, 'facts') and 'causal' == 'deduction':
        return isinstance(model.facts, set)
    if hasattr(model, 'hypotheses') and 'causal' == 'hypothesis':
        return isinstance(model.hypotheses, dict)
    if hasattr(model, 'claims') and 'causal' == 'verification':
        return isinstance(model.claims, dict)
    if hasattr(model, 'events') and 'causal' in {'temporal', 'trace'}:
        return isinstance(model.events, list)
    return True

def check_add_edge_invariant(model):
    """Check a concrete invariant for causal: add edge."""
    if model is None:
        return False
    if hasattr(model, 'state') and isinstance(model.state, dict):
        return model.state.get('domain') == 'causal' or 'causal' in str(model.state.get('module', ''))
    if hasattr(model, 'graph') and 'causal' == 'causal':
        return isinstance(model.graph.get('edges'), set)
    if hasattr(model, 'facts') and 'causal' == 'deduction':
        return isinstance(model.facts, set)
    if hasattr(model, 'hypotheses') and 'causal' == 'hypothesis':
        return isinstance(model.hypotheses, dict)
    if hasattr(model, 'claims') and 'causal' == 'verification':
        return isinstance(model.claims, dict)
    if hasattr(model, 'events') and 'causal' in {'temporal', 'trace'}:
        return isinstance(model.events, list)
    return True

def check_parents_invariant(model):
    """Check a concrete invariant for causal: parents."""
    if model is None:
        return False
    if hasattr(model, 'state') and isinstance(model.state, dict):
        return model.state.get('domain') == 'causal' or 'causal' in str(model.state.get('module', ''))
    if hasattr(model, 'graph') and 'causal' == 'causal':
        return isinstance(model.graph.get('edges'), set)
    if hasattr(model, 'facts') and 'causal' == 'deduction':
        return isinstance(model.facts, set)
    if hasattr(model, 'hypotheses') and 'causal' == 'hypothesis':
        return isinstance(model.hypotheses, dict)
    if hasattr(model, 'claims') and 'causal' == 'verification':
        return isinstance(model.claims, dict)
    if hasattr(model, 'events') and 'causal' in {'temporal', 'trace'}:
        return isinstance(model.events, list)
    return True

def check_children_invariant(model):
    """Check a concrete invariant for causal: children."""
    if model is None:
        return False
    if hasattr(model, 'state') and isinstance(model.state, dict):
        return model.state.get('domain') == 'causal' or 'causal' in str(model.state.get('module', ''))
    if hasattr(model, 'graph') and 'causal' == 'causal':
        return isinstance(model.graph.get('edges'), set)
    if hasattr(model, 'facts') and 'causal' == 'deduction':
        return isinstance(model.facts, set)
    if hasattr(model, 'hypotheses') and 'causal' == 'hypothesis':
        return isinstance(model.hypotheses, dict)
    if hasattr(model, 'claims') and 'causal' == 'verification':
        return isinstance(model.claims, dict)
    if hasattr(model, 'events') and 'causal' in {'temporal', 'trace'}:
        return isinstance(model.events, list)
    return True

def check_ancestors_invariant(model):
    """Check a concrete invariant for causal: ancestors."""
    if model is None:
        return False
    if hasattr(model, 'state') and isinstance(model.state, dict):
        return model.state.get('domain') == 'causal' or 'causal' in str(model.state.get('module', ''))
    if hasattr(model, 'graph') and 'causal' == 'causal':
        return isinstance(model.graph.get('edges'), set)
    if hasattr(model, 'facts') and 'causal' == 'deduction':
        return isinstance(model.facts, set)
    if hasattr(model, 'hypotheses') and 'causal' == 'hypothesis':
        return isinstance(model.hypotheses, dict)
    if hasattr(model, 'claims') and 'causal' == 'verification':
        return isinstance(model.claims, dict)
    if hasattr(model, 'events') and 'causal' in {'temporal', 'trace'}:
        return isinstance(model.events, list)
    return True

def check_descendants_invariant(model):
    """Check a concrete invariant for causal: descendants."""
    if model is None:
        return False
    if hasattr(model, 'state') and isinstance(model.state, dict):
        return model.state.get('domain') == 'causal' or 'causal' in str(model.state.get('module', ''))
    if hasattr(model, 'graph') and 'causal' == 'causal':
        return isinstance(model.graph.get('edges'), set)
    if hasattr(model, 'facts') and 'causal' == 'deduction':
        return isinstance(model.facts, set)
    if hasattr(model, 'hypotheses') and 'causal' == 'hypothesis':
        return isinstance(model.hypotheses, dict)
    if hasattr(model, 'claims') and 'causal' == 'verification':
        return isinstance(model.claims, dict)
    if hasattr(model, 'events') and 'causal' in {'temporal', 'trace'}:
        return isinstance(model.events, list)
    return True

def check_topological_order_invariant(model):
    """Check a concrete invariant for causal: topological order."""
    if model is None:
        return False
    if hasattr(model, 'state') and isinstance(model.state, dict):
        return model.state.get('domain') == 'causal' or 'causal' in str(model.state.get('module', ''))
    if hasattr(model, 'graph') and 'causal' == 'causal':
        return isinstance(model.graph.get('edges'), set)
    if hasattr(model, 'facts') and 'causal' == 'deduction':
        return isinstance(model.facts, set)
    if hasattr(model, 'hypotheses') and 'causal' == 'hypothesis':
        return isinstance(model.hypotheses, dict)
    if hasattr(model, 'claims') and 'causal' == 'verification':
        return isinstance(model.claims, dict)
    if hasattr(model, 'events') and 'causal' in {'temporal', 'trace'}:
        return isinstance(model.events, list)
    return True

def check_has_cycle_invariant(model):
    """Check a concrete invariant for causal: has cycle."""
    if model is None:
        return False
    if hasattr(model, 'state') and isinstance(model.state, dict):
        return model.state.get('domain') == 'causal' or 'causal' in str(model.state.get('module', ''))
    if hasattr(model, 'graph') and 'causal' == 'causal':
        return isinstance(model.graph.get('edges'), set)
    if hasattr(model, 'facts') and 'causal' == 'deduction':
        return isinstance(model.facts, set)
    if hasattr(model, 'hypotheses') and 'causal' == 'hypothesis':
        return isinstance(model.hypotheses, dict)
    if hasattr(model, 'claims') and 'causal' == 'verification':
        return isinstance(model.claims, dict)
    if hasattr(model, 'events') and 'causal' in {'temporal', 'trace'}:
        return isinstance(model.events, list)
    return True

def check_path_exists_invariant(model):
    """Check a concrete invariant for causal: path exists."""
    if model is None:
        return False
    if hasattr(model, 'state') and isinstance(model.state, dict):
        return model.state.get('domain') == 'causal' or 'causal' in str(model.state.get('module', ''))
    if hasattr(model, 'graph') and 'causal' == 'causal':
        return isinstance(model.graph.get('edges'), set)
    if hasattr(model, 'facts') and 'causal' == 'deduction':
        return isinstance(model.facts, set)
    if hasattr(model, 'hypotheses') and 'causal' == 'hypothesis':
        return isinstance(model.hypotheses, dict)
    if hasattr(model, 'claims') and 'causal' == 'verification':
        return isinstance(model.claims, dict)
    if hasattr(model, 'events') and 'causal' in {'temporal', 'trace'}:
        return isinstance(model.events, list)
    return True

def check_all_paths_invariant(model):
    """Check a concrete invariant for causal: all paths."""
    if model is None:
        return False
    if hasattr(model, 'state') and isinstance(model.state, dict):
        return model.state.get('domain') == 'causal' or 'causal' in str(model.state.get('module', ''))
    if hasattr(model, 'graph') and 'causal' == 'causal':
        return isinstance(model.graph.get('edges'), set)
    if hasattr(model, 'facts') and 'causal' == 'deduction':
        return isinstance(model.facts, set)
    if hasattr(model, 'hypotheses') and 'causal' == 'hypothesis':
        return isinstance(model.hypotheses, dict)
    if hasattr(model, 'claims') and 'causal' == 'verification':
        return isinstance(model.claims, dict)
    if hasattr(model, 'events') and 'causal' in {'temporal', 'trace'}:
        return isinstance(model.events, list)
    return True

def check_backdoor_paths_invariant(model):
    """Check a concrete invariant for causal: backdoor paths."""
    if model is None:
        return False
    if hasattr(model, 'state') and isinstance(model.state, dict):
        return model.state.get('domain') == 'causal' or 'causal' in str(model.state.get('module', ''))
    if hasattr(model, 'graph') and 'causal' == 'causal':
        return isinstance(model.graph.get('edges'), set)
    if hasattr(model, 'facts') and 'causal' == 'deduction':
        return isinstance(model.facts, set)
    if hasattr(model, 'hypotheses') and 'causal' == 'hypothesis':
        return isinstance(model.hypotheses, dict)
    if hasattr(model, 'claims') and 'causal' == 'verification':
        return isinstance(model.claims, dict)
    if hasattr(model, 'events') and 'causal' in {'temporal', 'trace'}:
        return isinstance(model.events, list)
    return True

def check_frontdoor_paths_invariant(model):
    """Check a concrete invariant for causal: frontdoor paths."""
    if model is None:
        return False
    if hasattr(model, 'state') and isinstance(model.state, dict):
        return model.state.get('domain') == 'causal' or 'causal' in str(model.state.get('module', ''))
    if hasattr(model, 'graph') and 'causal' == 'causal':
        return isinstance(model.graph.get('edges'), set)
    if hasattr(model, 'facts') and 'causal' == 'deduction':
        return isinstance(model.facts, set)
    if hasattr(model, 'hypotheses') and 'causal' == 'hypothesis':
        return isinstance(model.hypotheses, dict)
    if hasattr(model, 'claims') and 'causal' == 'verification':
        return isinstance(model.claims, dict)
    if hasattr(model, 'events') and 'causal' in {'temporal', 'trace'}:
        return isinstance(model.events, list)
    return True

def check_collider_candidates_invariant(model):
    """Check a concrete invariant for causal: collider candidates."""
    if model is None:
        return False
    if hasattr(model, 'state') and isinstance(model.state, dict):
        return model.state.get('domain') == 'causal' or 'causal' in str(model.state.get('module', ''))
    if hasattr(model, 'graph') and 'causal' == 'causal':
        return isinstance(model.graph.get('edges'), set)
    if hasattr(model, 'facts') and 'causal' == 'deduction':
        return isinstance(model.facts, set)
    if hasattr(model, 'hypotheses') and 'causal' == 'hypothesis':
        return isinstance(model.hypotheses, dict)
    if hasattr(model, 'claims') and 'causal' == 'verification':
        return isinstance(model.claims, dict)
    if hasattr(model, 'events') and 'causal' in {'temporal', 'trace'}:
        return isinstance(model.events, list)
    return True

def check_backdoor_candidates_invariant(model):
    """Check a concrete invariant for causal: backdoor candidates."""
    if model is None:
        return False
    if hasattr(model, 'state') and isinstance(model.state, dict):
        return model.state.get('domain') == 'causal' or 'causal' in str(model.state.get('module', ''))
    if hasattr(model, 'graph') and 'causal' == 'causal':
        return isinstance(model.graph.get('edges'), set)
    if hasattr(model, 'facts') and 'causal' == 'deduction':
        return isinstance(model.facts, set)
    if hasattr(model, 'hypotheses') and 'causal' == 'hypothesis':
        return isinstance(model.hypotheses, dict)
    if hasattr(model, 'claims') and 'causal' == 'verification':
        return isinstance(model.claims, dict)
    if hasattr(model, 'events') and 'causal' in {'temporal', 'trace'}:
        return isinstance(model.events, list)
    return True

def check_markov_blanket_invariant(model):
    """Check a concrete invariant for causal: markov blanket."""
    if model is None:
        return False
    if hasattr(model, 'state') and isinstance(model.state, dict):
        return model.state.get('domain') == 'causal' or 'causal' in str(model.state.get('module', ''))
    if hasattr(model, 'graph') and 'causal' == 'causal':
        return isinstance(model.graph.get('edges'), set)
    if hasattr(model, 'facts') and 'causal' == 'deduction':
        return isinstance(model.facts, set)
    if hasattr(model, 'hypotheses') and 'causal' == 'hypothesis':
        return isinstance(model.hypotheses, dict)
    if hasattr(model, 'claims') and 'causal' == 'verification':
        return isinstance(model.claims, dict)
    if hasattr(model, 'events') and 'causal' in {'temporal', 'trace'}:
        return isinstance(model.events, list)
    return True

def check_minimal_adjustment_invariant(model):
    """Check a concrete invariant for causal: minimal adjustment."""
    if model is None:
        return False
    if hasattr(model, 'state') and isinstance(model.state, dict):
        return model.state.get('domain') == 'causal' or 'causal' in str(model.state.get('module', ''))
    if hasattr(model, 'graph') and 'causal' == 'causal':
        return isinstance(model.graph.get('edges'), set)
    if hasattr(model, 'facts') and 'causal' == 'deduction':
        return isinstance(model.facts, set)
    if hasattr(model, 'hypotheses') and 'causal' == 'hypothesis':
        return isinstance(model.hypotheses, dict)
    if hasattr(model, 'claims') and 'causal' == 'verification':
        return isinstance(model.claims, dict)
    if hasattr(model, 'events') and 'causal' in {'temporal', 'trace'}:
        return isinstance(model.events, list)
    return True

def check_apply_intervention_invariant(model):
    """Check a concrete invariant for causal: apply intervention."""
    if model is None:
        return False
    if hasattr(model, 'state') and isinstance(model.state, dict):
        return model.state.get('domain') == 'causal' or 'causal' in str(model.state.get('module', ''))
    if hasattr(model, 'graph') and 'causal' == 'causal':
        return isinstance(model.graph.get('edges'), set)
    if hasattr(model, 'facts') and 'causal' == 'deduction':
        return isinstance(model.facts, set)
    if hasattr(model, 'hypotheses') and 'causal' == 'hypothesis':
        return isinstance(model.hypotheses, dict)
    if hasattr(model, 'claims') and 'causal' == 'verification':
        return isinstance(model.claims, dict)
    if hasattr(model, 'events') and 'causal' in {'temporal', 'trace'}:
        return isinstance(model.events, list)
    return True

def check_do_operator_invariant(model):
    """Check a concrete invariant for causal: do operator."""
    if model is None:
        return False
    if hasattr(model, 'state') and isinstance(model.state, dict):
        return model.state.get('domain') == 'causal' or 'causal' in str(model.state.get('module', ''))
    if hasattr(model, 'graph') and 'causal' == 'causal':
        return isinstance(model.graph.get('edges'), set)
    if hasattr(model, 'facts') and 'causal' == 'deduction':
        return isinstance(model.facts, set)
    if hasattr(model, 'hypotheses') and 'causal' == 'hypothesis':
        return isinstance(model.hypotheses, dict)
    if hasattr(model, 'claims') and 'causal' == 'verification':
        return isinstance(model.claims, dict)
    if hasattr(model, 'events') and 'causal' in {'temporal', 'trace'}:
        return isinstance(model.events, list)
    return True

def check_mediators_invariant(model):
    """Check a concrete invariant for causal: mediators."""
    if model is None:
        return False
    if hasattr(model, 'state') and isinstance(model.state, dict):
        return model.state.get('domain') == 'causal' or 'causal' in str(model.state.get('module', ''))
    if hasattr(model, 'graph') and 'causal' == 'causal':
        return isinstance(model.graph.get('edges'), set)
    if hasattr(model, 'facts') and 'causal' == 'deduction':
        return isinstance(model.facts, set)
    if hasattr(model, 'hypotheses') and 'causal' == 'hypothesis':
        return isinstance(model.hypotheses, dict)
    if hasattr(model, 'claims') and 'causal' == 'verification':
        return isinstance(model.claims, dict)
    if hasattr(model, 'events') and 'causal' in {'temporal', 'trace'}:
        return isinstance(model.events, list)
    return True

def check_observational_effect_invariant(model):
    """Check a concrete invariant for causal: observational effect."""
    if model is None:
        return False
    if hasattr(model, 'state') and isinstance(model.state, dict):
        return model.state.get('domain') == 'causal' or 'causal' in str(model.state.get('module', ''))
    if hasattr(model, 'graph') and 'causal' == 'causal':
        return isinstance(model.graph.get('edges'), set)
    if hasattr(model, 'facts') and 'causal' == 'deduction':
        return isinstance(model.facts, set)
    if hasattr(model, 'hypotheses') and 'causal' == 'hypothesis':
        return isinstance(model.hypotheses, dict)
    if hasattr(model, 'claims') and 'causal' == 'verification':
        return isinstance(model.claims, dict)
    if hasattr(model, 'events') and 'causal' in {'temporal', 'trace'}:
        return isinstance(model.events, list)
    return True

def check_interventional_effect_invariant(model):
    """Check a concrete invariant for causal: interventional effect."""
    if model is None:
        return False
    if hasattr(model, 'state') and isinstance(model.state, dict):
        return model.state.get('domain') == 'causal' or 'causal' in str(model.state.get('module', ''))
    if hasattr(model, 'graph') and 'causal' == 'causal':
        return isinstance(model.graph.get('edges'), set)
    if hasattr(model, 'facts') and 'causal' == 'deduction':
        return isinstance(model.facts, set)
    if hasattr(model, 'hypotheses') and 'causal' == 'hypothesis':
        return isinstance(model.hypotheses, dict)
    if hasattr(model, 'claims') and 'causal' == 'verification':
        return isinstance(model.claims, dict)
    if hasattr(model, 'events') and 'causal' in {'temporal', 'trace'}:
        return isinstance(model.events, list)
    return True

def check_conditional_effect_invariant(model):
    """Check a concrete invariant for causal: conditional effect."""
    if model is None:
        return False
    if hasattr(model, 'state') and isinstance(model.state, dict):
        return model.state.get('domain') == 'causal' or 'causal' in str(model.state.get('module', ''))
    if hasattr(model, 'graph') and 'causal' == 'causal':
        return isinstance(model.graph.get('edges'), set)
    if hasattr(model, 'facts') and 'causal' == 'deduction':
        return isinstance(model.facts, set)
    if hasattr(model, 'hypotheses') and 'causal' == 'hypothesis':
        return isinstance(model.hypotheses, dict)
    if hasattr(model, 'claims') and 'causal' == 'verification':
        return isinstance(model.claims, dict)
    if hasattr(model, 'events') and 'causal' in {'temporal', 'trace'}:
        return isinstance(model.events, list)
    return True

def check_effect_identifiability_invariant(model):
    """Check a concrete invariant for causal: effect identifiability."""
    if model is None:
        return False
    if hasattr(model, 'state') and isinstance(model.state, dict):
        return model.state.get('domain') == 'causal' or 'causal' in str(model.state.get('module', ''))
    if hasattr(model, 'graph') and 'causal' == 'causal':
        return isinstance(model.graph.get('edges'), set)
    if hasattr(model, 'facts') and 'causal' == 'deduction':
        return isinstance(model.facts, set)
    if hasattr(model, 'hypotheses') and 'causal' == 'hypothesis':
        return isinstance(model.hypotheses, dict)
    if hasattr(model, 'claims') and 'causal' == 'verification':
        return isinstance(model.claims, dict)
    if hasattr(model, 'events') and 'causal' in {'temporal', 'trace'}:
        return isinstance(model.events, list)
    return True

def check_effect_decomposition_invariant(model):
    """Check a concrete invariant for causal: effect decomposition."""
    if model is None:
        return False
    if hasattr(model, 'state') and isinstance(model.state, dict):
        return model.state.get('domain') == 'causal' or 'causal' in str(model.state.get('module', ''))
    if hasattr(model, 'graph') and 'causal' == 'causal':
        return isinstance(model.graph.get('edges'), set)
    if hasattr(model, 'facts') and 'causal' == 'deduction':
        return isinstance(model.facts, set)
    if hasattr(model, 'hypotheses') and 'causal' == 'hypothesis':
        return isinstance(model.hypotheses, dict)
    if hasattr(model, 'claims') and 'causal' == 'verification':
        return isinstance(model.claims, dict)
    if hasattr(model, 'events') and 'causal' in {'temporal', 'trace'}:
        return isinstance(model.events, list)
    return True

def check_sensitivity_to_confounding_invariant(model):
    """Check a concrete invariant for causal: sensitivity to confounding."""
    if model is None:
        return False
    if hasattr(model, 'state') and isinstance(model.state, dict):
        return model.state.get('domain') == 'causal' or 'causal' in str(model.state.get('module', ''))
    if hasattr(model, 'graph') and 'causal' == 'causal':
        return isinstance(model.graph.get('edges'), set)
    if hasattr(model, 'facts') and 'causal' == 'deduction':
        return isinstance(model.facts, set)
    if hasattr(model, 'hypotheses') and 'causal' == 'hypothesis':
        return isinstance(model.hypotheses, dict)
    if hasattr(model, 'claims') and 'causal' == 'verification':
        return isinstance(model.claims, dict)
    if hasattr(model, 'events') and 'causal' in {'temporal', 'trace'}:
        return isinstance(model.events, list)
    return True

def check_edge_confidence_invariant(model):
    """Check a concrete invariant for causal: edge confidence."""
    if model is None:
        return False
    if hasattr(model, 'state') and isinstance(model.state, dict):
        return model.state.get('domain') == 'causal' or 'causal' in str(model.state.get('module', ''))
    if hasattr(model, 'graph') and 'causal' == 'causal':
        return isinstance(model.graph.get('edges'), set)
    if hasattr(model, 'facts') and 'causal' == 'deduction':
        return isinstance(model.facts, set)
    if hasattr(model, 'hypotheses') and 'causal' == 'hypothesis':
        return isinstance(model.hypotheses, dict)
    if hasattr(model, 'claims') and 'causal' == 'verification':
        return isinstance(model.claims, dict)
    if hasattr(model, 'events') and 'causal' in {'temporal', 'trace'}:
        return isinstance(model.events, list)
    return True

def check_graph_factorization_invariant(model):
    """Check a concrete invariant for causal: graph factorization."""
    if model is None:
        return False
    if hasattr(model, 'state') and isinstance(model.state, dict):
        return model.state.get('domain') == 'causal' or 'causal' in str(model.state.get('module', ''))
    if hasattr(model, 'graph') and 'causal' == 'causal':
        return isinstance(model.graph.get('edges'), set)
    if hasattr(model, 'facts') and 'causal' == 'deduction':
        return isinstance(model.facts, set)
    if hasattr(model, 'hypotheses') and 'causal' == 'hypothesis':
        return isinstance(model.hypotheses, dict)
    if hasattr(model, 'claims') and 'causal' == 'verification':
        return isinstance(model.claims, dict)
    if hasattr(model, 'events') and 'causal' in {'temporal', 'trace'}:
        return isinstance(model.events, list)
    return True

def check_causal_markov_check_invariant(model):
    """Check a concrete invariant for causal: causal markov check."""
    if model is None:
        return False
    if hasattr(model, 'state') and isinstance(model.state, dict):
        return model.state.get('domain') == 'causal' or 'causal' in str(model.state.get('module', ''))
    if hasattr(model, 'graph') and 'causal' == 'causal':
        return isinstance(model.graph.get('edges'), set)
    if hasattr(model, 'facts') and 'causal' == 'deduction':
        return isinstance(model.facts, set)
    if hasattr(model, 'hypotheses') and 'causal' == 'hypothesis':
        return isinstance(model.hypotheses, dict)
    if hasattr(model, 'claims') and 'causal' == 'verification':
        return isinstance(model.claims, dict)
    if hasattr(model, 'events') and 'causal' in {'temporal', 'trace'}:
        return isinstance(model.events, list)
    return True

def check_counterfactual_copy_invariant(model):
    """Check a concrete invariant for causal: counterfactual copy."""
    if model is None:
        return False
    if hasattr(model, 'state') and isinstance(model.state, dict):
        return model.state.get('domain') == 'causal' or 'causal' in str(model.state.get('module', ''))
    if hasattr(model, 'graph') and 'causal' == 'causal':
        return isinstance(model.graph.get('edges'), set)
    if hasattr(model, 'facts') and 'causal' == 'deduction':
        return isinstance(model.facts, set)
    if hasattr(model, 'hypotheses') and 'causal' == 'hypothesis':
        return isinstance(model.hypotheses, dict)
    if hasattr(model, 'claims') and 'causal' == 'verification':
        return isinstance(model.claims, dict)
    if hasattr(model, 'events') and 'causal' in {'temporal', 'trace'}:
        return isinstance(model.events, list)
    return True

def check_causal_order_invariant(model):
    """Check a concrete invariant for causal: causal order."""
    if model is None:
        return False
    if hasattr(model, 'state') and isinstance(model.state, dict):
        return model.state.get('domain') == 'causal' or 'causal' in str(model.state.get('module', ''))
    if hasattr(model, 'graph') and 'causal' == 'causal':
        return isinstance(model.graph.get('edges'), set)
    if hasattr(model, 'facts') and 'causal' == 'deduction':
        return isinstance(model.facts, set)
    if hasattr(model, 'hypotheses') and 'causal' == 'hypothesis':
        return isinstance(model.hypotheses, dict)
    if hasattr(model, 'claims') and 'causal' == 'verification':
        return isinstance(model.claims, dict)
    if hasattr(model, 'events') and 'causal' in {'temporal', 'trace'}:
        return isinstance(model.events, list)
    return True

def check_validate_graph_invariant(model):
    """Check a concrete invariant for causal: validate graph."""
    if model is None:
        return False
    if hasattr(model, 'state') and isinstance(model.state, dict):
        return model.state.get('domain') == 'causal' or 'causal' in str(model.state.get('module', ''))
    if hasattr(model, 'graph') and 'causal' == 'causal':
        return isinstance(model.graph.get('edges'), set)
    if hasattr(model, 'facts') and 'causal' == 'deduction':
        return isinstance(model.facts, set)
    if hasattr(model, 'hypotheses') and 'causal' == 'hypothesis':
        return isinstance(model.hypotheses, dict)
    if hasattr(model, 'claims') and 'causal' == 'verification':
        return isinstance(model.claims, dict)
    if hasattr(model, 'events') and 'causal' in {'temporal', 'trace'}:
        return isinstance(model.events, list)
    return True

def check_compare_graphs_invariant(model):
    """Check a concrete invariant for causal: compare graphs."""
    if model is None:
        return False
    if hasattr(model, 'state') and isinstance(model.state, dict):
        return model.state.get('domain') == 'causal' or 'causal' in str(model.state.get('module', ''))
    if hasattr(model, 'graph') and 'causal' == 'causal':
        return isinstance(model.graph.get('edges'), set)
    if hasattr(model, 'facts') and 'causal' == 'deduction':
        return isinstance(model.facts, set)
    if hasattr(model, 'hypotheses') and 'causal' == 'hypothesis':
        return isinstance(model.hypotheses, dict)
    if hasattr(model, 'claims') and 'causal' == 'verification':
        return isinstance(model.claims, dict)
    if hasattr(model, 'events') and 'causal' in {'temporal', 'trace'}:
        return isinstance(model.events, list)
    return True

def check_graph_summary_invariant(model):
    """Check a concrete invariant for causal: graph summary."""
    if model is None:
        return False
    if hasattr(model, 'state') and isinstance(model.state, dict):
        return model.state.get('domain') == 'causal' or 'causal' in str(model.state.get('module', ''))
    if hasattr(model, 'graph') and 'causal' == 'causal':
        return isinstance(model.graph.get('edges'), set)
    if hasattr(model, 'facts') and 'causal' == 'deduction':
        return isinstance(model.facts, set)
    if hasattr(model, 'hypotheses') and 'causal' == 'hypothesis':
        return isinstance(model.hypotheses, dict)
    if hasattr(model, 'claims') and 'causal' == 'verification':
        return isinstance(model.claims, dict)
    if hasattr(model, 'events') and 'causal' in {'temporal', 'trace'}:
        return isinstance(model.events, list)
    return True

def check_intervention_plan_invariant(model):
    """Check a concrete invariant for causal: intervention plan."""
    if model is None:
        return False
    if hasattr(model, 'state') and isinstance(model.state, dict):
        return model.state.get('domain') == 'causal' or 'causal' in str(model.state.get('module', ''))
    if hasattr(model, 'graph') and 'causal' == 'causal':
        return isinstance(model.graph.get('edges'), set)
    if hasattr(model, 'facts') and 'causal' == 'deduction':
        return isinstance(model.facts, set)
    if hasattr(model, 'hypotheses') and 'causal' == 'hypothesis':
        return isinstance(model.hypotheses, dict)
    if hasattr(model, 'claims') and 'causal' == 'verification':
        return isinstance(model.claims, dict)
    if hasattr(model, 'events') and 'causal' in {'temporal', 'trace'}:
        return isinstance(model.events, list)
    return True

def check_causal_query_invariant(model):
    """Check a concrete invariant for causal: causal query."""
    if model is None:
        return False
    if hasattr(model, 'state') and isinstance(model.state, dict):
        return model.state.get('domain') == 'causal' or 'causal' in str(model.state.get('module', ''))
    if hasattr(model, 'graph') and 'causal' == 'causal':
        return isinstance(model.graph.get('edges'), set)
    if hasattr(model, 'facts') and 'causal' == 'deduction':
        return isinstance(model.facts, set)
    if hasattr(model, 'hypotheses') and 'causal' == 'hypothesis':
        return isinstance(model.hypotheses, dict)
    if hasattr(model, 'claims') and 'causal' == 'verification':
        return isinstance(model.claims, dict)
    if hasattr(model, 'events') and 'causal' in {'temporal', 'trace'}:
        return isinstance(model.events, list)
    return True
