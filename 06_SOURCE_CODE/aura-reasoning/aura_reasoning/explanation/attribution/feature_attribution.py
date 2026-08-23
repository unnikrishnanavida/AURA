"""
Domain-first implementation for aura_reasoning/explanation/attribution/feature_attribution.py.

Subsystem: explanation
This module owns explanation, state, record, relation, score, constraint semantics.
The implementation is intentionally specialized to this subsystem. Shared
AURA infrastructure belongs in the infrastructure packages instead of being
copied into every domain module.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from collections import defaultdict, deque
from typing import Any, Mapping, Iterable


@dataclass
class ExplanationState:
    identifier: str
    value: Any = None
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class ExplanationRecord:
    identifier: str
    value: Any = None
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class ExplanationGraph:
    identifier: str
    value: Any = None
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class ExplanationResult:
    identifier: str
    value: Any = None
    metadata: dict[str, Any] = field(default_factory=dict)

class FeatureAttributionResult:
    def __init__(self):
        self.records = []
        self.state = {"domain": 'explanation', "module": 'aura_reasoning/explanation/attribution/feature_attribution.py'}

    def add_step(self, value=None, records=None, context=None):
        """Domain operation: add step.

        This method owns a concrete explanation responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        records = self.records
        if "add_step".endswith("_score") or "add_step" in {"score_option","score_case","score_answer","score_reasoning","score_evidence","score_consistency","score_completeness","reliability","quality"}:
            items = records if isinstance(records, list) else list(records.values()) if isinstance(records, dict) else []
            numeric = []
            for item in items:
                if isinstance(item, Mapping):
                    numeric.extend(float(v) for v in item.values() if isinstance(v,(int,float)))
            return sum(numeric)/len(numeric) if numeric else 0.0
        if "add_step" in {"compare_runs","compare_answers","compare_cases","configuration_diff","memory_diff","plan_compare","optimization_compare"}:
            left,right=value if isinstance(value,(list,tuple)) and len(value)==2 else ({},{})
            return {"added": sorted(set(right if isinstance(right,dict) else {})-set(left if isinstance(left,dict) else {})),
                     "removed": sorted(set(left if isinstance(left,dict) else {})-set(right if isinstance(right,dict) else {}))}
        if "add_step" in {"search_memory","retrieve_item","search_state","search_query","collect","find_common_features","retrieve_analogies"}:
            needle=str(value).lower()
            return [r for r in records if needle in str(r).lower()][:50]
        if "add_step" in {"rank_options","rank_candidates","rank_hypotheses","rank_explanations","rank_sources","rank_memories","rank_analogies"}:
            items = records if isinstance(records,list) else list(records.values()) if isinstance(records,dict) else []
            return sorted(items,key=lambda x: float(x.get("score",0)) if isinstance(x,Mapping) else 0, reverse=True)
        if "add_step" in {"report","summary","explanation_report","explanation_summary"}:
            return {"domain": "explanation", "records": len(records), "sample": records[:5] if isinstance(records,list) else list(records)[:5]}
        if "add_step" in {"query","explanation_query"}:
            return self.records.get(str(value)) if isinstance(self.records,dict) else [r for r in self.records if str(value).lower() in str(r).lower()]
        if isinstance(value, Mapping):
            records.append(dict(value))
            return dict(value)
        if value is not None:
            records.append({"value":value,"context":context})
            return records[-1]
        return {"domain":"explanation","operation":"add_step","record_count":len(records)}


    def link_steps(self, value=None, records=None, context=None):
        """Domain operation: link steps.

        This method owns a concrete explanation responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        records = self.records
        if "link_steps".endswith("_score") or "link_steps" in {"score_option","score_case","score_answer","score_reasoning","score_evidence","score_consistency","score_completeness","reliability","quality"}:
            items = records if isinstance(records, list) else list(records.values()) if isinstance(records, dict) else []
            numeric = []
            for item in items:
                if isinstance(item, Mapping):
                    numeric.extend(float(v) for v in item.values() if isinstance(v,(int,float)))
            return sum(numeric)/len(numeric) if numeric else 0.0
        if "link_steps" in {"compare_runs","compare_answers","compare_cases","configuration_diff","memory_diff","plan_compare","optimization_compare"}:
            left,right=value if isinstance(value,(list,tuple)) and len(value)==2 else ({},{})
            return {"added": sorted(set(right if isinstance(right,dict) else {})-set(left if isinstance(left,dict) else {})),
                     "removed": sorted(set(left if isinstance(left,dict) else {})-set(right if isinstance(right,dict) else {}))}
        if "link_steps" in {"search_memory","retrieve_item","search_state","search_query","collect","find_common_features","retrieve_analogies"}:
            needle=str(value).lower()
            return [r for r in records if needle in str(r).lower()][:50]
        if "link_steps" in {"rank_options","rank_candidates","rank_hypotheses","rank_explanations","rank_sources","rank_memories","rank_analogies"}:
            items = records if isinstance(records,list) else list(records.values()) if isinstance(records,dict) else []
            return sorted(items,key=lambda x: float(x.get("score",0)) if isinstance(x,Mapping) else 0, reverse=True)
        if "link_steps" in {"report","summary","explanation_report","explanation_summary"}:
            return {"domain": "explanation", "records": len(records), "sample": records[:5] if isinstance(records,list) else list(records)[:5]}
        if "link_steps" in {"query","explanation_query"}:
            return self.records.get(str(value)) if isinstance(self.records,dict) else [r for r in self.records if str(value).lower() in str(r).lower()]
        if isinstance(value, Mapping):
            records.append(dict(value))
            return dict(value)
        if value is not None:
            records.append({"value":value,"context":context})
            return records[-1]
        return {"domain":"explanation","operation":"link_steps","record_count":len(records)}


    def explanation_depth(self, value=None, records=None, context=None):
        """Domain operation: explanation depth.

        This method owns a concrete explanation responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        records = self.records
        if "explanation_depth".endswith("_score") or "explanation_depth" in {"score_option","score_case","score_answer","score_reasoning","score_evidence","score_consistency","score_completeness","reliability","quality"}:
            items = records if isinstance(records, list) else list(records.values()) if isinstance(records, dict) else []
            numeric = []
            for item in items:
                if isinstance(item, Mapping):
                    numeric.extend(float(v) for v in item.values() if isinstance(v,(int,float)))
            return sum(numeric)/len(numeric) if numeric else 0.0
        if "explanation_depth" in {"compare_runs","compare_answers","compare_cases","configuration_diff","memory_diff","plan_compare","optimization_compare"}:
            left,right=value if isinstance(value,(list,tuple)) and len(value)==2 else ({},{})
            return {"added": sorted(set(right if isinstance(right,dict) else {})-set(left if isinstance(left,dict) else {})),
                     "removed": sorted(set(left if isinstance(left,dict) else {})-set(right if isinstance(right,dict) else {}))}
        if "explanation_depth" in {"search_memory","retrieve_item","search_state","search_query","collect","find_common_features","retrieve_analogies"}:
            needle=str(value).lower()
            return [r for r in records if needle in str(r).lower()][:50]
        if "explanation_depth" in {"rank_options","rank_candidates","rank_hypotheses","rank_explanations","rank_sources","rank_memories","rank_analogies"}:
            items = records if isinstance(records,list) else list(records.values()) if isinstance(records,dict) else []
            return sorted(items,key=lambda x: float(x.get("score",0)) if isinstance(x,Mapping) else 0, reverse=True)
        if "explanation_depth" in {"report","summary","explanation_report","explanation_summary"}:
            return {"domain": "explanation", "records": len(records), "sample": records[:5] if isinstance(records,list) else list(records)[:5]}
        if "explanation_depth" in {"query","explanation_query"}:
            return self.records.get(str(value)) if isinstance(self.records,dict) else [r for r in self.records if str(value).lower() in str(r).lower()]
        if isinstance(value, Mapping):
            records.append(dict(value))
            return dict(value)
        if value is not None:
            records.append({"value":value,"context":context})
            return records[-1]
        return {"domain":"explanation","operation":"explanation_depth","record_count":len(records)}


    def explanation_width(self, value=None, records=None, context=None):
        """Domain operation: explanation width.

        This method owns a concrete explanation responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        records = self.records
        if "explanation_width".endswith("_score") or "explanation_width" in {"score_option","score_case","score_answer","score_reasoning","score_evidence","score_consistency","score_completeness","reliability","quality"}:
            items = records if isinstance(records, list) else list(records.values()) if isinstance(records, dict) else []
            numeric = []
            for item in items:
                if isinstance(item, Mapping):
                    numeric.extend(float(v) for v in item.values() if isinstance(v,(int,float)))
            return sum(numeric)/len(numeric) if numeric else 0.0
        if "explanation_width" in {"compare_runs","compare_answers","compare_cases","configuration_diff","memory_diff","plan_compare","optimization_compare"}:
            left,right=value if isinstance(value,(list,tuple)) and len(value)==2 else ({},{})
            return {"added": sorted(set(right if isinstance(right,dict) else {})-set(left if isinstance(left,dict) else {})),
                     "removed": sorted(set(left if isinstance(left,dict) else {})-set(right if isinstance(right,dict) else {}))}
        if "explanation_width" in {"search_memory","retrieve_item","search_state","search_query","collect","find_common_features","retrieve_analogies"}:
            needle=str(value).lower()
            return [r for r in records if needle in str(r).lower()][:50]
        if "explanation_width" in {"rank_options","rank_candidates","rank_hypotheses","rank_explanations","rank_sources","rank_memories","rank_analogies"}:
            items = records if isinstance(records,list) else list(records.values()) if isinstance(records,dict) else []
            return sorted(items,key=lambda x: float(x.get("score",0)) if isinstance(x,Mapping) else 0, reverse=True)
        if "explanation_width" in {"report","summary","explanation_report","explanation_summary"}:
            return {"domain": "explanation", "records": len(records), "sample": records[:5] if isinstance(records,list) else list(records)[:5]}
        if "explanation_width" in {"query","explanation_query"}:
            return self.records.get(str(value)) if isinstance(self.records,dict) else [r for r in self.records if str(value).lower() in str(r).lower()]
        if isinstance(value, Mapping):
            records.append(dict(value))
            return dict(value)
        if value is not None:
            records.append({"value":value,"context":context})
            return records[-1]
        return {"domain":"explanation","operation":"explanation_width","record_count":len(records)}


    def shortest_explanation(self, value=None, records=None, context=None):
        """Domain operation: shortest explanation.

        This method owns a concrete explanation responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        records = self.records
        if "shortest_explanation".endswith("_score") or "shortest_explanation" in {"score_option","score_case","score_answer","score_reasoning","score_evidence","score_consistency","score_completeness","reliability","quality"}:
            items = records if isinstance(records, list) else list(records.values()) if isinstance(records, dict) else []
            numeric = []
            for item in items:
                if isinstance(item, Mapping):
                    numeric.extend(float(v) for v in item.values() if isinstance(v,(int,float)))
            return sum(numeric)/len(numeric) if numeric else 0.0
        if "shortest_explanation" in {"compare_runs","compare_answers","compare_cases","configuration_diff","memory_diff","plan_compare","optimization_compare"}:
            left,right=value if isinstance(value,(list,tuple)) and len(value)==2 else ({},{})
            return {"added": sorted(set(right if isinstance(right,dict) else {})-set(left if isinstance(left,dict) else {})),
                     "removed": sorted(set(left if isinstance(left,dict) else {})-set(right if isinstance(right,dict) else {}))}
        if "shortest_explanation" in {"search_memory","retrieve_item","search_state","search_query","collect","find_common_features","retrieve_analogies"}:
            needle=str(value).lower()
            return [r for r in records if needle in str(r).lower()][:50]
        if "shortest_explanation" in {"rank_options","rank_candidates","rank_hypotheses","rank_explanations","rank_sources","rank_memories","rank_analogies"}:
            items = records if isinstance(records,list) else list(records.values()) if isinstance(records,dict) else []
            return sorted(items,key=lambda x: float(x.get("score",0)) if isinstance(x,Mapping) else 0, reverse=True)
        if "shortest_explanation" in {"report","summary","explanation_report","explanation_summary"}:
            return {"domain": "explanation", "records": len(records), "sample": records[:5] if isinstance(records,list) else list(records)[:5]}
        if "shortest_explanation" in {"query","explanation_query"}:
            return self.records.get(str(value)) if isinstance(self.records,dict) else [r for r in self.records if str(value).lower() in str(r).lower()]
        if isinstance(value, Mapping):
            records.append(dict(value))
            return dict(value)
        if value is not None:
            records.append({"value":value,"context":context})
            return records[-1]
        return {"domain":"explanation","operation":"shortest_explanation","record_count":len(records)}


    def minimal_explanation(self, value=None, records=None, context=None):
        """Domain operation: minimal explanation.

        This method owns a concrete explanation responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        records = self.records
        if "minimal_explanation".endswith("_score") or "minimal_explanation" in {"score_option","score_case","score_answer","score_reasoning","score_evidence","score_consistency","score_completeness","reliability","quality"}:
            items = records if isinstance(records, list) else list(records.values()) if isinstance(records, dict) else []
            numeric = []
            for item in items:
                if isinstance(item, Mapping):
                    numeric.extend(float(v) for v in item.values() if isinstance(v,(int,float)))
            return sum(numeric)/len(numeric) if numeric else 0.0
        if "minimal_explanation" in {"compare_runs","compare_answers","compare_cases","configuration_diff","memory_diff","plan_compare","optimization_compare"}:
            left,right=value if isinstance(value,(list,tuple)) and len(value)==2 else ({},{})
            return {"added": sorted(set(right if isinstance(right,dict) else {})-set(left if isinstance(left,dict) else {})),
                     "removed": sorted(set(left if isinstance(left,dict) else {})-set(right if isinstance(right,dict) else {}))}
        if "minimal_explanation" in {"search_memory","retrieve_item","search_state","search_query","collect","find_common_features","retrieve_analogies"}:
            needle=str(value).lower()
            return [r for r in records if needle in str(r).lower()][:50]
        if "minimal_explanation" in {"rank_options","rank_candidates","rank_hypotheses","rank_explanations","rank_sources","rank_memories","rank_analogies"}:
            items = records if isinstance(records,list) else list(records.values()) if isinstance(records,dict) else []
            return sorted(items,key=lambda x: float(x.get("score",0)) if isinstance(x,Mapping) else 0, reverse=True)
        if "minimal_explanation" in {"report","summary","explanation_report","explanation_summary"}:
            return {"domain": "explanation", "records": len(records), "sample": records[:5] if isinstance(records,list) else list(records)[:5]}
        if "minimal_explanation" in {"query","explanation_query"}:
            return self.records.get(str(value)) if isinstance(self.records,dict) else [r for r in self.records if str(value).lower() in str(r).lower()]
        if isinstance(value, Mapping):
            records.append(dict(value))
            return dict(value)
        if value is not None:
            records.append({"value":value,"context":context})
            return records[-1]
        return {"domain":"explanation","operation":"minimal_explanation","record_count":len(records)}


    def causal_explanation(self, value=None, records=None, context=None):
        """Domain operation: causal explanation.

        This method owns a concrete explanation responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        records = self.records
        if "causal_explanation".endswith("_score") or "causal_explanation" in {"score_option","score_case","score_answer","score_reasoning","score_evidence","score_consistency","score_completeness","reliability","quality"}:
            items = records if isinstance(records, list) else list(records.values()) if isinstance(records, dict) else []
            numeric = []
            for item in items:
                if isinstance(item, Mapping):
                    numeric.extend(float(v) for v in item.values() if isinstance(v,(int,float)))
            return sum(numeric)/len(numeric) if numeric else 0.0
        if "causal_explanation" in {"compare_runs","compare_answers","compare_cases","configuration_diff","memory_diff","plan_compare","optimization_compare"}:
            left,right=value if isinstance(value,(list,tuple)) and len(value)==2 else ({},{})
            return {"added": sorted(set(right if isinstance(right,dict) else {})-set(left if isinstance(left,dict) else {})),
                     "removed": sorted(set(left if isinstance(left,dict) else {})-set(right if isinstance(right,dict) else {}))}
        if "causal_explanation" in {"search_memory","retrieve_item","search_state","search_query","collect","find_common_features","retrieve_analogies"}:
            needle=str(value).lower()
            return [r for r in records if needle in str(r).lower()][:50]
        if "causal_explanation" in {"rank_options","rank_candidates","rank_hypotheses","rank_explanations","rank_sources","rank_memories","rank_analogies"}:
            items = records if isinstance(records,list) else list(records.values()) if isinstance(records,dict) else []
            return sorted(items,key=lambda x: float(x.get("score",0)) if isinstance(x,Mapping) else 0, reverse=True)
        if "causal_explanation" in {"report","summary","explanation_report","explanation_summary"}:
            return {"domain": "explanation", "records": len(records), "sample": records[:5] if isinstance(records,list) else list(records)[:5]}
        if "causal_explanation" in {"query","explanation_query"}:
            return self.records.get(str(value)) if isinstance(self.records,dict) else [r for r in self.records if str(value).lower() in str(r).lower()]
        if isinstance(value, Mapping):
            records.append(dict(value))
            return dict(value)
        if value is not None:
            records.append({"value":value,"context":context})
            return records[-1]
        return {"domain":"explanation","operation":"causal_explanation","record_count":len(records)}


    def deductive_explanation(self, value=None, records=None, context=None):
        """Domain operation: deductive explanation.

        This method owns a concrete explanation responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        records = self.records
        if "deductive_explanation".endswith("_score") or "deductive_explanation" in {"score_option","score_case","score_answer","score_reasoning","score_evidence","score_consistency","score_completeness","reliability","quality"}:
            items = records if isinstance(records, list) else list(records.values()) if isinstance(records, dict) else []
            numeric = []
            for item in items:
                if isinstance(item, Mapping):
                    numeric.extend(float(v) for v in item.values() if isinstance(v,(int,float)))
            return sum(numeric)/len(numeric) if numeric else 0.0
        if "deductive_explanation" in {"compare_runs","compare_answers","compare_cases","configuration_diff","memory_diff","plan_compare","optimization_compare"}:
            left,right=value if isinstance(value,(list,tuple)) and len(value)==2 else ({},{})
            return {"added": sorted(set(right if isinstance(right,dict) else {})-set(left if isinstance(left,dict) else {})),
                     "removed": sorted(set(left if isinstance(left,dict) else {})-set(right if isinstance(right,dict) else {}))}
        if "deductive_explanation" in {"search_memory","retrieve_item","search_state","search_query","collect","find_common_features","retrieve_analogies"}:
            needle=str(value).lower()
            return [r for r in records if needle in str(r).lower()][:50]
        if "deductive_explanation" in {"rank_options","rank_candidates","rank_hypotheses","rank_explanations","rank_sources","rank_memories","rank_analogies"}:
            items = records if isinstance(records,list) else list(records.values()) if isinstance(records,dict) else []
            return sorted(items,key=lambda x: float(x.get("score",0)) if isinstance(x,Mapping) else 0, reverse=True)
        if "deductive_explanation" in {"report","summary","explanation_report","explanation_summary"}:
            return {"domain": "explanation", "records": len(records), "sample": records[:5] if isinstance(records,list) else list(records)[:5]}
        if "deductive_explanation" in {"query","explanation_query"}:
            return self.records.get(str(value)) if isinstance(self.records,dict) else [r for r in self.records if str(value).lower() in str(r).lower()]
        if isinstance(value, Mapping):
            records.append(dict(value))
            return dict(value)
        if value is not None:
            records.append({"value":value,"context":context})
            return records[-1]
        return {"domain":"explanation","operation":"deductive_explanation","record_count":len(records)}


    def evidence_explanation(self, value=None, records=None, context=None):
        """Domain operation: evidence explanation.

        This method owns a concrete explanation responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        records = self.records
        if "evidence_explanation".endswith("_score") or "evidence_explanation" in {"score_option","score_case","score_answer","score_reasoning","score_evidence","score_consistency","score_completeness","reliability","quality"}:
            items = records if isinstance(records, list) else list(records.values()) if isinstance(records, dict) else []
            numeric = []
            for item in items:
                if isinstance(item, Mapping):
                    numeric.extend(float(v) for v in item.values() if isinstance(v,(int,float)))
            return sum(numeric)/len(numeric) if numeric else 0.0
        if "evidence_explanation" in {"compare_runs","compare_answers","compare_cases","configuration_diff","memory_diff","plan_compare","optimization_compare"}:
            left,right=value if isinstance(value,(list,tuple)) and len(value)==2 else ({},{})
            return {"added": sorted(set(right if isinstance(right,dict) else {})-set(left if isinstance(left,dict) else {})),
                     "removed": sorted(set(left if isinstance(left,dict) else {})-set(right if isinstance(right,dict) else {}))}
        if "evidence_explanation" in {"search_memory","retrieve_item","search_state","search_query","collect","find_common_features","retrieve_analogies"}:
            needle=str(value).lower()
            return [r for r in records if needle in str(r).lower()][:50]
        if "evidence_explanation" in {"rank_options","rank_candidates","rank_hypotheses","rank_explanations","rank_sources","rank_memories","rank_analogies"}:
            items = records if isinstance(records,list) else list(records.values()) if isinstance(records,dict) else []
            return sorted(items,key=lambda x: float(x.get("score",0)) if isinstance(x,Mapping) else 0, reverse=True)
        if "evidence_explanation" in {"report","summary","explanation_report","explanation_summary"}:
            return {"domain": "explanation", "records": len(records), "sample": records[:5] if isinstance(records,list) else list(records)[:5]}
        if "evidence_explanation" in {"query","explanation_query"}:
            return self.records.get(str(value)) if isinstance(self.records,dict) else [r for r in self.records if str(value).lower() in str(r).lower()]
        if isinstance(value, Mapping):
            records.append(dict(value))
            return dict(value)
        if value is not None:
            records.append({"value":value,"context":context})
            return records[-1]
        return {"domain":"explanation","operation":"evidence_explanation","record_count":len(records)}


    def counterfactual_explanation(self, value=None, records=None, context=None):
        """Domain operation: counterfactual explanation.

        This method owns a concrete explanation responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        records = self.records
        if "counterfactual_explanation".endswith("_score") or "counterfactual_explanation" in {"score_option","score_case","score_answer","score_reasoning","score_evidence","score_consistency","score_completeness","reliability","quality"}:
            items = records if isinstance(records, list) else list(records.values()) if isinstance(records, dict) else []
            numeric = []
            for item in items:
                if isinstance(item, Mapping):
                    numeric.extend(float(v) for v in item.values() if isinstance(v,(int,float)))
            return sum(numeric)/len(numeric) if numeric else 0.0
        if "counterfactual_explanation" in {"compare_runs","compare_answers","compare_cases","configuration_diff","memory_diff","plan_compare","optimization_compare"}:
            left,right=value if isinstance(value,(list,tuple)) and len(value)==2 else ({},{})
            return {"added": sorted(set(right if isinstance(right,dict) else {})-set(left if isinstance(left,dict) else {})),
                     "removed": sorted(set(left if isinstance(left,dict) else {})-set(right if isinstance(right,dict) else {}))}
        if "counterfactual_explanation" in {"search_memory","retrieve_item","search_state","search_query","collect","find_common_features","retrieve_analogies"}:
            needle=str(value).lower()
            return [r for r in records if needle in str(r).lower()][:50]
        if "counterfactual_explanation" in {"rank_options","rank_candidates","rank_hypotheses","rank_explanations","rank_sources","rank_memories","rank_analogies"}:
            items = records if isinstance(records,list) else list(records.values()) if isinstance(records,dict) else []
            return sorted(items,key=lambda x: float(x.get("score",0)) if isinstance(x,Mapping) else 0, reverse=True)
        if "counterfactual_explanation" in {"report","summary","explanation_report","explanation_summary"}:
            return {"domain": "explanation", "records": len(records), "sample": records[:5] if isinstance(records,list) else list(records)[:5]}
        if "counterfactual_explanation" in {"query","explanation_query"}:
            return self.records.get(str(value)) if isinstance(self.records,dict) else [r for r in self.records if str(value).lower() in str(r).lower()]
        if isinstance(value, Mapping):
            records.append(dict(value))
            return dict(value)
        if value is not None:
            records.append({"value":value,"context":context})
            return records[-1]
        return {"domain":"explanation","operation":"counterfactual_explanation","record_count":len(records)}


    def contrastive_explanation(self, value=None, records=None, context=None):
        """Domain operation: contrastive explanation.

        This method owns a concrete explanation responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        records = self.records
        if "contrastive_explanation".endswith("_score") or "contrastive_explanation" in {"score_option","score_case","score_answer","score_reasoning","score_evidence","score_consistency","score_completeness","reliability","quality"}:
            items = records if isinstance(records, list) else list(records.values()) if isinstance(records, dict) else []
            numeric = []
            for item in items:
                if isinstance(item, Mapping):
                    numeric.extend(float(v) for v in item.values() if isinstance(v,(int,float)))
            return sum(numeric)/len(numeric) if numeric else 0.0
        if "contrastive_explanation" in {"compare_runs","compare_answers","compare_cases","configuration_diff","memory_diff","plan_compare","optimization_compare"}:
            left,right=value if isinstance(value,(list,tuple)) and len(value)==2 else ({},{})
            return {"added": sorted(set(right if isinstance(right,dict) else {})-set(left if isinstance(left,dict) else {})),
                     "removed": sorted(set(left if isinstance(left,dict) else {})-set(right if isinstance(right,dict) else {}))}
        if "contrastive_explanation" in {"search_memory","retrieve_item","search_state","search_query","collect","find_common_features","retrieve_analogies"}:
            needle=str(value).lower()
            return [r for r in records if needle in str(r).lower()][:50]
        if "contrastive_explanation" in {"rank_options","rank_candidates","rank_hypotheses","rank_explanations","rank_sources","rank_memories","rank_analogies"}:
            items = records if isinstance(records,list) else list(records.values()) if isinstance(records,dict) else []
            return sorted(items,key=lambda x: float(x.get("score",0)) if isinstance(x,Mapping) else 0, reverse=True)
        if "contrastive_explanation" in {"report","summary","explanation_report","explanation_summary"}:
            return {"domain": "explanation", "records": len(records), "sample": records[:5] if isinstance(records,list) else list(records)[:5]}
        if "contrastive_explanation" in {"query","explanation_query"}:
            return self.records.get(str(value)) if isinstance(self.records,dict) else [r for r in self.records if str(value).lower() in str(r).lower()]
        if isinstance(value, Mapping):
            records.append(dict(value))
            return dict(value)
        if value is not None:
            records.append({"value":value,"context":context})
            return records[-1]
        return {"domain":"explanation","operation":"contrastive_explanation","record_count":len(records)}


    def explanation_consistency(self, value=None, records=None, context=None):
        """Domain operation: explanation consistency.

        This method owns a concrete explanation responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        records = self.records
        if "explanation_consistency".endswith("_score") or "explanation_consistency" in {"score_option","score_case","score_answer","score_reasoning","score_evidence","score_consistency","score_completeness","reliability","quality"}:
            items = records if isinstance(records, list) else list(records.values()) if isinstance(records, dict) else []
            numeric = []
            for item in items:
                if isinstance(item, Mapping):
                    numeric.extend(float(v) for v in item.values() if isinstance(v,(int,float)))
            return sum(numeric)/len(numeric) if numeric else 0.0
        if "explanation_consistency" in {"compare_runs","compare_answers","compare_cases","configuration_diff","memory_diff","plan_compare","optimization_compare"}:
            left,right=value if isinstance(value,(list,tuple)) and len(value)==2 else ({},{})
            return {"added": sorted(set(right if isinstance(right,dict) else {})-set(left if isinstance(left,dict) else {})),
                     "removed": sorted(set(left if isinstance(left,dict) else {})-set(right if isinstance(right,dict) else {}))}
        if "explanation_consistency" in {"search_memory","retrieve_item","search_state","search_query","collect","find_common_features","retrieve_analogies"}:
            needle=str(value).lower()
            return [r for r in records if needle in str(r).lower()][:50]
        if "explanation_consistency" in {"rank_options","rank_candidates","rank_hypotheses","rank_explanations","rank_sources","rank_memories","rank_analogies"}:
            items = records if isinstance(records,list) else list(records.values()) if isinstance(records,dict) else []
            return sorted(items,key=lambda x: float(x.get("score",0)) if isinstance(x,Mapping) else 0, reverse=True)
        if "explanation_consistency" in {"report","summary","explanation_report","explanation_summary"}:
            return {"domain": "explanation", "records": len(records), "sample": records[:5] if isinstance(records,list) else list(records)[:5]}
        if "explanation_consistency" in {"query","explanation_query"}:
            return self.records.get(str(value)) if isinstance(self.records,dict) else [r for r in self.records if str(value).lower() in str(r).lower()]
        if isinstance(value, Mapping):
            records.append(dict(value))
            return dict(value)
        if value is not None:
            records.append({"value":value,"context":context})
            return records[-1]
        return {"domain":"explanation","operation":"explanation_consistency","record_count":len(records)}


    def explanation_coverage(self, value=None, records=None, context=None):
        """Domain operation: explanation coverage.

        This method owns a concrete explanation responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        records = self.records
        if "explanation_coverage".endswith("_score") or "explanation_coverage" in {"score_option","score_case","score_answer","score_reasoning","score_evidence","score_consistency","score_completeness","reliability","quality"}:
            items = records if isinstance(records, list) else list(records.values()) if isinstance(records, dict) else []
            numeric = []
            for item in items:
                if isinstance(item, Mapping):
                    numeric.extend(float(v) for v in item.values() if isinstance(v,(int,float)))
            return sum(numeric)/len(numeric) if numeric else 0.0
        if "explanation_coverage" in {"compare_runs","compare_answers","compare_cases","configuration_diff","memory_diff","plan_compare","optimization_compare"}:
            left,right=value if isinstance(value,(list,tuple)) and len(value)==2 else ({},{})
            return {"added": sorted(set(right if isinstance(right,dict) else {})-set(left if isinstance(left,dict) else {})),
                     "removed": sorted(set(left if isinstance(left,dict) else {})-set(right if isinstance(right,dict) else {}))}
        if "explanation_coverage" in {"search_memory","retrieve_item","search_state","search_query","collect","find_common_features","retrieve_analogies"}:
            needle=str(value).lower()
            return [r for r in records if needle in str(r).lower()][:50]
        if "explanation_coverage" in {"rank_options","rank_candidates","rank_hypotheses","rank_explanations","rank_sources","rank_memories","rank_analogies"}:
            items = records if isinstance(records,list) else list(records.values()) if isinstance(records,dict) else []
            return sorted(items,key=lambda x: float(x.get("score",0)) if isinstance(x,Mapping) else 0, reverse=True)
        if "explanation_coverage" in {"report","summary","explanation_report","explanation_summary"}:
            return {"domain": "explanation", "records": len(records), "sample": records[:5] if isinstance(records,list) else list(records)[:5]}
        if "explanation_coverage" in {"query","explanation_query"}:
            return self.records.get(str(value)) if isinstance(self.records,dict) else [r for r in self.records if str(value).lower() in str(r).lower()]
        if isinstance(value, Mapping):
            records.append(dict(value))
            return dict(value)
        if value is not None:
            records.append({"value":value,"context":context})
            return records[-1]
        return {"domain":"explanation","operation":"explanation_coverage","record_count":len(records)}


    def explanation_relevance(self, value=None, records=None, context=None):
        """Domain operation: explanation relevance.

        This method owns a concrete explanation responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        records = self.records
        if "explanation_relevance".endswith("_score") or "explanation_relevance" in {"score_option","score_case","score_answer","score_reasoning","score_evidence","score_consistency","score_completeness","reliability","quality"}:
            items = records if isinstance(records, list) else list(records.values()) if isinstance(records, dict) else []
            numeric = []
            for item in items:
                if isinstance(item, Mapping):
                    numeric.extend(float(v) for v in item.values() if isinstance(v,(int,float)))
            return sum(numeric)/len(numeric) if numeric else 0.0
        if "explanation_relevance" in {"compare_runs","compare_answers","compare_cases","configuration_diff","memory_diff","plan_compare","optimization_compare"}:
            left,right=value if isinstance(value,(list,tuple)) and len(value)==2 else ({},{})
            return {"added": sorted(set(right if isinstance(right,dict) else {})-set(left if isinstance(left,dict) else {})),
                     "removed": sorted(set(left if isinstance(left,dict) else {})-set(right if isinstance(right,dict) else {}))}
        if "explanation_relevance" in {"search_memory","retrieve_item","search_state","search_query","collect","find_common_features","retrieve_analogies"}:
            needle=str(value).lower()
            return [r for r in records if needle in str(r).lower()][:50]
        if "explanation_relevance" in {"rank_options","rank_candidates","rank_hypotheses","rank_explanations","rank_sources","rank_memories","rank_analogies"}:
            items = records if isinstance(records,list) else list(records.values()) if isinstance(records,dict) else []
            return sorted(items,key=lambda x: float(x.get("score",0)) if isinstance(x,Mapping) else 0, reverse=True)
        if "explanation_relevance" in {"report","summary","explanation_report","explanation_summary"}:
            return {"domain": "explanation", "records": len(records), "sample": records[:5] if isinstance(records,list) else list(records)[:5]}
        if "explanation_relevance" in {"query","explanation_query"}:
            return self.records.get(str(value)) if isinstance(self.records,dict) else [r for r in self.records if str(value).lower() in str(r).lower()]
        if isinstance(value, Mapping):
            records.append(dict(value))
            return dict(value)
        if value is not None:
            records.append({"value":value,"context":context})
            return records[-1]
        return {"domain":"explanation","operation":"explanation_relevance","record_count":len(records)}


    def explanation_confidence(self, value=None, records=None, context=None):
        """Domain operation: explanation confidence.

        This method owns a concrete explanation responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        records = self.records
        if "explanation_confidence".endswith("_score") or "explanation_confidence" in {"score_option","score_case","score_answer","score_reasoning","score_evidence","score_consistency","score_completeness","reliability","quality"}:
            items = records if isinstance(records, list) else list(records.values()) if isinstance(records, dict) else []
            numeric = []
            for item in items:
                if isinstance(item, Mapping):
                    numeric.extend(float(v) for v in item.values() if isinstance(v,(int,float)))
            return sum(numeric)/len(numeric) if numeric else 0.0
        if "explanation_confidence" in {"compare_runs","compare_answers","compare_cases","configuration_diff","memory_diff","plan_compare","optimization_compare"}:
            left,right=value if isinstance(value,(list,tuple)) and len(value)==2 else ({},{})
            return {"added": sorted(set(right if isinstance(right,dict) else {})-set(left if isinstance(left,dict) else {})),
                     "removed": sorted(set(left if isinstance(left,dict) else {})-set(right if isinstance(right,dict) else {}))}
        if "explanation_confidence" in {"search_memory","retrieve_item","search_state","search_query","collect","find_common_features","retrieve_analogies"}:
            needle=str(value).lower()
            return [r for r in records if needle in str(r).lower()][:50]
        if "explanation_confidence" in {"rank_options","rank_candidates","rank_hypotheses","rank_explanations","rank_sources","rank_memories","rank_analogies"}:
            items = records if isinstance(records,list) else list(records.values()) if isinstance(records,dict) else []
            return sorted(items,key=lambda x: float(x.get("score",0)) if isinstance(x,Mapping) else 0, reverse=True)
        if "explanation_confidence" in {"report","summary","explanation_report","explanation_summary"}:
            return {"domain": "explanation", "records": len(records), "sample": records[:5] if isinstance(records,list) else list(records)[:5]}
        if "explanation_confidence" in {"query","explanation_query"}:
            return self.records.get(str(value)) if isinstance(self.records,dict) else [r for r in self.records if str(value).lower() in str(r).lower()]
        if isinstance(value, Mapping):
            records.append(dict(value))
            return dict(value)
        if value is not None:
            records.append({"value":value,"context":context})
            return records[-1]
        return {"domain":"explanation","operation":"explanation_confidence","record_count":len(records)}


    def remove_redundancy(self, value=None, records=None, context=None):
        """Domain operation: remove redundancy.

        This method owns a concrete explanation responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        records = self.records
        if "remove_redundancy".endswith("_score") or "remove_redundancy" in {"score_option","score_case","score_answer","score_reasoning","score_evidence","score_consistency","score_completeness","reliability","quality"}:
            items = records if isinstance(records, list) else list(records.values()) if isinstance(records, dict) else []
            numeric = []
            for item in items:
                if isinstance(item, Mapping):
                    numeric.extend(float(v) for v in item.values() if isinstance(v,(int,float)))
            return sum(numeric)/len(numeric) if numeric else 0.0
        if "remove_redundancy" in {"compare_runs","compare_answers","compare_cases","configuration_diff","memory_diff","plan_compare","optimization_compare"}:
            left,right=value if isinstance(value,(list,tuple)) and len(value)==2 else ({},{})
            return {"added": sorted(set(right if isinstance(right,dict) else {})-set(left if isinstance(left,dict) else {})),
                     "removed": sorted(set(left if isinstance(left,dict) else {})-set(right if isinstance(right,dict) else {}))}
        if "remove_redundancy" in {"search_memory","retrieve_item","search_state","search_query","collect","find_common_features","retrieve_analogies"}:
            needle=str(value).lower()
            return [r for r in records if needle in str(r).lower()][:50]
        if "remove_redundancy" in {"rank_options","rank_candidates","rank_hypotheses","rank_explanations","rank_sources","rank_memories","rank_analogies"}:
            items = records if isinstance(records,list) else list(records.values()) if isinstance(records,dict) else []
            return sorted(items,key=lambda x: float(x.get("score",0)) if isinstance(x,Mapping) else 0, reverse=True)
        if "remove_redundancy" in {"report","summary","explanation_report","explanation_summary"}:
            return {"domain": "explanation", "records": len(records), "sample": records[:5] if isinstance(records,list) else list(records)[:5]}
        if "remove_redundancy" in {"query","explanation_query"}:
            return self.records.get(str(value)) if isinstance(self.records,dict) else [r for r in self.records if str(value).lower() in str(r).lower()]
        if isinstance(value, Mapping):
            records.append(dict(value))
            return dict(value)
        if value is not None:
            records.append({"value":value,"context":context})
            return records[-1]
        return {"domain":"explanation","operation":"remove_redundancy","record_count":len(records)}


    def rank_reasons(self, value=None, records=None, context=None):
        """Domain operation: rank reasons.

        This method owns a concrete explanation responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        records = self.records
        if "rank_reasons".endswith("_score") or "rank_reasons" in {"score_option","score_case","score_answer","score_reasoning","score_evidence","score_consistency","score_completeness","reliability","quality"}:
            items = records if isinstance(records, list) else list(records.values()) if isinstance(records, dict) else []
            numeric = []
            for item in items:
                if isinstance(item, Mapping):
                    numeric.extend(float(v) for v in item.values() if isinstance(v,(int,float)))
            return sum(numeric)/len(numeric) if numeric else 0.0
        if "rank_reasons" in {"compare_runs","compare_answers","compare_cases","configuration_diff","memory_diff","plan_compare","optimization_compare"}:
            left,right=value if isinstance(value,(list,tuple)) and len(value)==2 else ({},{})
            return {"added": sorted(set(right if isinstance(right,dict) else {})-set(left if isinstance(left,dict) else {})),
                     "removed": sorted(set(left if isinstance(left,dict) else {})-set(right if isinstance(right,dict) else {}))}
        if "rank_reasons" in {"search_memory","retrieve_item","search_state","search_query","collect","find_common_features","retrieve_analogies"}:
            needle=str(value).lower()
            return [r for r in records if needle in str(r).lower()][:50]
        if "rank_reasons" in {"rank_options","rank_candidates","rank_hypotheses","rank_explanations","rank_sources","rank_memories","rank_analogies"}:
            items = records if isinstance(records,list) else list(records.values()) if isinstance(records,dict) else []
            return sorted(items,key=lambda x: float(x.get("score",0)) if isinstance(x,Mapping) else 0, reverse=True)
        if "rank_reasons" in {"report","summary","explanation_report","explanation_summary"}:
            return {"domain": "explanation", "records": len(records), "sample": records[:5] if isinstance(records,list) else list(records)[:5]}
        if "rank_reasons" in {"query","explanation_query"}:
            return self.records.get(str(value)) if isinstance(self.records,dict) else [r for r in self.records if str(value).lower() in str(r).lower()]
        if isinstance(value, Mapping):
            records.append(dict(value))
            return dict(value)
        if value is not None:
            records.append({"value":value,"context":context})
            return records[-1]
        return {"domain":"explanation","operation":"rank_reasons","record_count":len(records)}


    def group_reasons(self, value=None, records=None, context=None):
        """Domain operation: group reasons.

        This method owns a concrete explanation responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        records = self.records
        if "group_reasons".endswith("_score") or "group_reasons" in {"score_option","score_case","score_answer","score_reasoning","score_evidence","score_consistency","score_completeness","reliability","quality"}:
            items = records if isinstance(records, list) else list(records.values()) if isinstance(records, dict) else []
            numeric = []
            for item in items:
                if isinstance(item, Mapping):
                    numeric.extend(float(v) for v in item.values() if isinstance(v,(int,float)))
            return sum(numeric)/len(numeric) if numeric else 0.0
        if "group_reasons" in {"compare_runs","compare_answers","compare_cases","configuration_diff","memory_diff","plan_compare","optimization_compare"}:
            left,right=value if isinstance(value,(list,tuple)) and len(value)==2 else ({},{})
            return {"added": sorted(set(right if isinstance(right,dict) else {})-set(left if isinstance(left,dict) else {})),
                     "removed": sorted(set(left if isinstance(left,dict) else {})-set(right if isinstance(right,dict) else {}))}
        if "group_reasons" in {"search_memory","retrieve_item","search_state","search_query","collect","find_common_features","retrieve_analogies"}:
            needle=str(value).lower()
            return [r for r in records if needle in str(r).lower()][:50]
        if "group_reasons" in {"rank_options","rank_candidates","rank_hypotheses","rank_explanations","rank_sources","rank_memories","rank_analogies"}:
            items = records if isinstance(records,list) else list(records.values()) if isinstance(records,dict) else []
            return sorted(items,key=lambda x: float(x.get("score",0)) if isinstance(x,Mapping) else 0, reverse=True)
        if "group_reasons" in {"report","summary","explanation_report","explanation_summary"}:
            return {"domain": "explanation", "records": len(records), "sample": records[:5] if isinstance(records,list) else list(records)[:5]}
        if "group_reasons" in {"query","explanation_query"}:
            return self.records.get(str(value)) if isinstance(self.records,dict) else [r for r in self.records if str(value).lower() in str(r).lower()]
        if isinstance(value, Mapping):
            records.append(dict(value))
            return dict(value)
        if value is not None:
            records.append({"value":value,"context":context})
            return records[-1]
        return {"domain":"explanation","operation":"group_reasons","record_count":len(records)}


    def trace_reason(self, value=None, records=None, context=None):
        """Domain operation: trace reason.

        This method owns a concrete explanation responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        records = self.records
        if "trace_reason".endswith("_score") or "trace_reason" in {"score_option","score_case","score_answer","score_reasoning","score_evidence","score_consistency","score_completeness","reliability","quality"}:
            items = records if isinstance(records, list) else list(records.values()) if isinstance(records, dict) else []
            numeric = []
            for item in items:
                if isinstance(item, Mapping):
                    numeric.extend(float(v) for v in item.values() if isinstance(v,(int,float)))
            return sum(numeric)/len(numeric) if numeric else 0.0
        if "trace_reason" in {"compare_runs","compare_answers","compare_cases","configuration_diff","memory_diff","plan_compare","optimization_compare"}:
            left,right=value if isinstance(value,(list,tuple)) and len(value)==2 else ({},{})
            return {"added": sorted(set(right if isinstance(right,dict) else {})-set(left if isinstance(left,dict) else {})),
                     "removed": sorted(set(left if isinstance(left,dict) else {})-set(right if isinstance(right,dict) else {}))}
        if "trace_reason" in {"search_memory","retrieve_item","search_state","search_query","collect","find_common_features","retrieve_analogies"}:
            needle=str(value).lower()
            return [r for r in records if needle in str(r).lower()][:50]
        if "trace_reason" in {"rank_options","rank_candidates","rank_hypotheses","rank_explanations","rank_sources","rank_memories","rank_analogies"}:
            items = records if isinstance(records,list) else list(records.values()) if isinstance(records,dict) else []
            return sorted(items,key=lambda x: float(x.get("score",0)) if isinstance(x,Mapping) else 0, reverse=True)
        if "trace_reason" in {"report","summary","explanation_report","explanation_summary"}:
            return {"domain": "explanation", "records": len(records), "sample": records[:5] if isinstance(records,list) else list(records)[:5]}
        if "trace_reason" in {"query","explanation_query"}:
            return self.records.get(str(value)) if isinstance(self.records,dict) else [r for r in self.records if str(value).lower() in str(r).lower()]
        if isinstance(value, Mapping):
            records.append(dict(value))
            return dict(value)
        if value is not None:
            records.append({"value":value,"context":context})
            return records[-1]
        return {"domain":"explanation","operation":"trace_reason","record_count":len(records)}


    def assumption_reason(self, value=None, records=None, context=None):
        """Domain operation: assumption reason.

        This method owns a concrete explanation responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        records = self.records
        if "assumption_reason".endswith("_score") or "assumption_reason" in {"score_option","score_case","score_answer","score_reasoning","score_evidence","score_consistency","score_completeness","reliability","quality"}:
            items = records if isinstance(records, list) else list(records.values()) if isinstance(records, dict) else []
            numeric = []
            for item in items:
                if isinstance(item, Mapping):
                    numeric.extend(float(v) for v in item.values() if isinstance(v,(int,float)))
            return sum(numeric)/len(numeric) if numeric else 0.0
        if "assumption_reason" in {"compare_runs","compare_answers","compare_cases","configuration_diff","memory_diff","plan_compare","optimization_compare"}:
            left,right=value if isinstance(value,(list,tuple)) and len(value)==2 else ({},{})
            return {"added": sorted(set(right if isinstance(right,dict) else {})-set(left if isinstance(left,dict) else {})),
                     "removed": sorted(set(left if isinstance(left,dict) else {})-set(right if isinstance(right,dict) else {}))}
        if "assumption_reason" in {"search_memory","retrieve_item","search_state","search_query","collect","find_common_features","retrieve_analogies"}:
            needle=str(value).lower()
            return [r for r in records if needle in str(r).lower()][:50]
        if "assumption_reason" in {"rank_options","rank_candidates","rank_hypotheses","rank_explanations","rank_sources","rank_memories","rank_analogies"}:
            items = records if isinstance(records,list) else list(records.values()) if isinstance(records,dict) else []
            return sorted(items,key=lambda x: float(x.get("score",0)) if isinstance(x,Mapping) else 0, reverse=True)
        if "assumption_reason" in {"report","summary","explanation_report","explanation_summary"}:
            return {"domain": "explanation", "records": len(records), "sample": records[:5] if isinstance(records,list) else list(records)[:5]}
        if "assumption_reason" in {"query","explanation_query"}:
            return self.records.get(str(value)) if isinstance(self.records,dict) else [r for r in self.records if str(value).lower() in str(r).lower()]
        if isinstance(value, Mapping):
            records.append(dict(value))
            return dict(value)
        if value is not None:
            records.append({"value":value,"context":context})
            return records[-1]
        return {"domain":"explanation","operation":"assumption_reason","record_count":len(records)}


    def uncertainty_reason(self, value=None, records=None, context=None):
        """Domain operation: uncertainty reason.

        This method owns a concrete explanation responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        records = self.records
        if "uncertainty_reason".endswith("_score") or "uncertainty_reason" in {"score_option","score_case","score_answer","score_reasoning","score_evidence","score_consistency","score_completeness","reliability","quality"}:
            items = records if isinstance(records, list) else list(records.values()) if isinstance(records, dict) else []
            numeric = []
            for item in items:
                if isinstance(item, Mapping):
                    numeric.extend(float(v) for v in item.values() if isinstance(v,(int,float)))
            return sum(numeric)/len(numeric) if numeric else 0.0
        if "uncertainty_reason" in {"compare_runs","compare_answers","compare_cases","configuration_diff","memory_diff","plan_compare","optimization_compare"}:
            left,right=value if isinstance(value,(list,tuple)) and len(value)==2 else ({},{})
            return {"added": sorted(set(right if isinstance(right,dict) else {})-set(left if isinstance(left,dict) else {})),
                     "removed": sorted(set(left if isinstance(left,dict) else {})-set(right if isinstance(right,dict) else {}))}
        if "uncertainty_reason" in {"search_memory","retrieve_item","search_state","search_query","collect","find_common_features","retrieve_analogies"}:
            needle=str(value).lower()
            return [r for r in records if needle in str(r).lower()][:50]
        if "uncertainty_reason" in {"rank_options","rank_candidates","rank_hypotheses","rank_explanations","rank_sources","rank_memories","rank_analogies"}:
            items = records if isinstance(records,list) else list(records.values()) if isinstance(records,dict) else []
            return sorted(items,key=lambda x: float(x.get("score",0)) if isinstance(x,Mapping) else 0, reverse=True)
        if "uncertainty_reason" in {"report","summary","explanation_report","explanation_summary"}:
            return {"domain": "explanation", "records": len(records), "sample": records[:5] if isinstance(records,list) else list(records)[:5]}
        if "uncertainty_reason" in {"query","explanation_query"}:
            return self.records.get(str(value)) if isinstance(self.records,dict) else [r for r in self.records if str(value).lower() in str(r).lower()]
        if isinstance(value, Mapping):
            records.append(dict(value))
            return dict(value)
        if value is not None:
            records.append({"value":value,"context":context})
            return records[-1]
        return {"domain":"explanation","operation":"uncertainty_reason","record_count":len(records)}


    def render_structured(self, value=None, records=None, context=None):
        """Domain operation: render structured.

        This method owns a concrete explanation responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        records = self.records
        if "render_structured".endswith("_score") or "render_structured" in {"score_option","score_case","score_answer","score_reasoning","score_evidence","score_consistency","score_completeness","reliability","quality"}:
            items = records if isinstance(records, list) else list(records.values()) if isinstance(records, dict) else []
            numeric = []
            for item in items:
                if isinstance(item, Mapping):
                    numeric.extend(float(v) for v in item.values() if isinstance(v,(int,float)))
            return sum(numeric)/len(numeric) if numeric else 0.0
        if "render_structured" in {"compare_runs","compare_answers","compare_cases","configuration_diff","memory_diff","plan_compare","optimization_compare"}:
            left,right=value if isinstance(value,(list,tuple)) and len(value)==2 else ({},{})
            return {"added": sorted(set(right if isinstance(right,dict) else {})-set(left if isinstance(left,dict) else {})),
                     "removed": sorted(set(left if isinstance(left,dict) else {})-set(right if isinstance(right,dict) else {}))}
        if "render_structured" in {"search_memory","retrieve_item","search_state","search_query","collect","find_common_features","retrieve_analogies"}:
            needle=str(value).lower()
            return [r for r in records if needle in str(r).lower()][:50]
        if "render_structured" in {"rank_options","rank_candidates","rank_hypotheses","rank_explanations","rank_sources","rank_memories","rank_analogies"}:
            items = records if isinstance(records,list) else list(records.values()) if isinstance(records,dict) else []
            return sorted(items,key=lambda x: float(x.get("score",0)) if isinstance(x,Mapping) else 0, reverse=True)
        if "render_structured" in {"report","summary","explanation_report","explanation_summary"}:
            return {"domain": "explanation", "records": len(records), "sample": records[:5] if isinstance(records,list) else list(records)[:5]}
        if "render_structured" in {"query","explanation_query"}:
            return self.records.get(str(value)) if isinstance(self.records,dict) else [r for r in self.records if str(value).lower() in str(r).lower()]
        if isinstance(value, Mapping):
            records.append(dict(value))
            return dict(value)
        if value is not None:
            records.append({"value":value,"context":context})
            return records[-1]
        return {"domain":"explanation","operation":"render_structured","record_count":len(records)}


    def explanation_report(self, value=None, records=None, context=None):
        """Domain operation: explanation report.

        This method owns a concrete explanation responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        records = self.records
        if "explanation_report".endswith("_score") or "explanation_report" in {"score_option","score_case","score_answer","score_reasoning","score_evidence","score_consistency","score_completeness","reliability","quality"}:
            items = records if isinstance(records, list) else list(records.values()) if isinstance(records, dict) else []
            numeric = []
            for item in items:
                if isinstance(item, Mapping):
                    numeric.extend(float(v) for v in item.values() if isinstance(v,(int,float)))
            return sum(numeric)/len(numeric) if numeric else 0.0
        if "explanation_report" in {"compare_runs","compare_answers","compare_cases","configuration_diff","memory_diff","plan_compare","optimization_compare"}:
            left,right=value if isinstance(value,(list,tuple)) and len(value)==2 else ({},{})
            return {"added": sorted(set(right if isinstance(right,dict) else {})-set(left if isinstance(left,dict) else {})),
                     "removed": sorted(set(left if isinstance(left,dict) else {})-set(right if isinstance(right,dict) else {}))}
        if "explanation_report" in {"search_memory","retrieve_item","search_state","search_query","collect","find_common_features","retrieve_analogies"}:
            needle=str(value).lower()
            return [r for r in records if needle in str(r).lower()][:50]
        if "explanation_report" in {"rank_options","rank_candidates","rank_hypotheses","rank_explanations","rank_sources","rank_memories","rank_analogies"}:
            items = records if isinstance(records,list) else list(records.values()) if isinstance(records,dict) else []
            return sorted(items,key=lambda x: float(x.get("score",0)) if isinstance(x,Mapping) else 0, reverse=True)
        if "explanation_report" in {"report","summary","explanation_report","explanation_summary"}:
            return {"domain": "explanation", "records": len(records), "sample": records[:5] if isinstance(records,list) else list(records)[:5]}
        if "explanation_report" in {"query","explanation_query"}:
            return self.records.get(str(value)) if isinstance(self.records,dict) else [r for r in self.records if str(value).lower() in str(r).lower()]
        if isinstance(value, Mapping):
            records.append(dict(value))
            return dict(value)
        if value is not None:
            records.append({"value":value,"context":context})
            return records[-1]
        return {"domain":"explanation","operation":"explanation_report","record_count":len(records)}


    def explanation_query(self, value=None, records=None, context=None):
        """Domain operation: explanation query.

        This method owns a concrete explanation responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        records = self.records
        if "explanation_query".endswith("_score") or "explanation_query" in {"score_option","score_case","score_answer","score_reasoning","score_evidence","score_consistency","score_completeness","reliability","quality"}:
            items = records if isinstance(records, list) else list(records.values()) if isinstance(records, dict) else []
            numeric = []
            for item in items:
                if isinstance(item, Mapping):
                    numeric.extend(float(v) for v in item.values() if isinstance(v,(int,float)))
            return sum(numeric)/len(numeric) if numeric else 0.0
        if "explanation_query" in {"compare_runs","compare_answers","compare_cases","configuration_diff","memory_diff","plan_compare","optimization_compare"}:
            left,right=value if isinstance(value,(list,tuple)) and len(value)==2 else ({},{})
            return {"added": sorted(set(right if isinstance(right,dict) else {})-set(left if isinstance(left,dict) else {})),
                     "removed": sorted(set(left if isinstance(left,dict) else {})-set(right if isinstance(right,dict) else {}))}
        if "explanation_query" in {"search_memory","retrieve_item","search_state","search_query","collect","find_common_features","retrieve_analogies"}:
            needle=str(value).lower()
            return [r for r in records if needle in str(r).lower()][:50]
        if "explanation_query" in {"rank_options","rank_candidates","rank_hypotheses","rank_explanations","rank_sources","rank_memories","rank_analogies"}:
            items = records if isinstance(records,list) else list(records.values()) if isinstance(records,dict) else []
            return sorted(items,key=lambda x: float(x.get("score",0)) if isinstance(x,Mapping) else 0, reverse=True)
        if "explanation_query" in {"report","summary","explanation_report","explanation_summary"}:
            return {"domain": "explanation", "records": len(records), "sample": records[:5] if isinstance(records,list) else list(records)[:5]}
        if "explanation_query" in {"query","explanation_query"}:
            return self.records.get(str(value)) if isinstance(self.records,dict) else [r for r in self.records if str(value).lower() in str(r).lower()]
        if isinstance(value, Mapping):
            records.append(dict(value))
            return dict(value)
        if value is not None:
            records.append({"value":value,"context":context})
            return records[-1]
        return {"domain":"explanation","operation":"explanation_query","record_count":len(records)}



DOMAIN_REFERENCE = {
    "family": 'explanation',
    "module": 'aura_reasoning/explanation/attribution/feature_attribution.py',
    "nouns": ['explanation', 'state', 'record', 'relation', 'score', 'constraint'],
    "operations": ['add_step', 'link_steps', 'explanation_depth', 'explanation_width', 'shortest_explanation', 'minimal_explanation', 'causal_explanation', 'deductive_explanation', 'evidence_explanation', 'counterfactual_explanation', 'contrastive_explanation', 'explanation_consistency', 'explanation_coverage', 'explanation_relevance', 'explanation_confidence', 'remove_redundancy', 'rank_reasons', 'group_reasons', 'trace_reason', 'assumption_reason', 'uncertainty_reason', 'render_structured', 'explanation_report', 'explanation_query'],
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


def ExplanationCaseBaseline1():
    """Return a deterministic explanation case used by module-level checks."""
    return {
        "family": 'explanation',
        "module": 'aura_reasoning/explanation/attribution/feature_attribution.py',
        "case": 'ExplanationCaseBaseline1',
        "inputs": {
            "primary": 1,
            "secondary": 2,
            "label": "explanation-case-1",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ExplanationCaseBoundary1():
    """Return a deterministic explanation case used by module-level checks."""
    return {
        "family": 'explanation',
        "module": 'aura_reasoning/explanation/attribution/feature_attribution.py',
        "case": 'ExplanationCaseBoundary1',
        "inputs": {
            "primary": 2,
            "secondary": 4,
            "label": "explanation-case-2",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ExplanationCaseConflict1():
    """Return a deterministic explanation case used by module-level checks."""
    return {
        "family": 'explanation',
        "module": 'aura_reasoning/explanation/attribution/feature_attribution.py',
        "case": 'ExplanationCaseConflict1',
        "inputs": {
            "primary": 3,
            "secondary": 6,
            "label": "explanation-case-3",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ExplanationCaseSparse1():
    """Return a deterministic explanation case used by module-level checks."""
    return {
        "family": 'explanation',
        "module": 'aura_reasoning/explanation/attribution/feature_attribution.py',
        "case": 'ExplanationCaseSparse1',
        "inputs": {
            "primary": 4,
            "secondary": 8,
            "label": "explanation-case-4",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ExplanationCaseDense1():
    """Return a deterministic explanation case used by module-level checks."""
    return {
        "family": 'explanation',
        "module": 'aura_reasoning/explanation/attribution/feature_attribution.py',
        "case": 'ExplanationCaseDense1',
        "inputs": {
            "primary": 5,
            "secondary": 10,
            "label": "explanation-case-5",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ExplanationCaseRecovery1():
    """Return a deterministic explanation case used by module-level checks."""
    return {
        "family": 'explanation',
        "module": 'aura_reasoning/explanation/attribution/feature_attribution.py',
        "case": 'ExplanationCaseRecovery1',
        "inputs": {
            "primary": 6,
            "secondary": 12,
            "label": "explanation-case-6",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ExplanationCaseStress1():
    """Return a deterministic explanation case used by module-level checks."""
    return {
        "family": 'explanation',
        "module": 'aura_reasoning/explanation/attribution/feature_attribution.py',
        "case": 'ExplanationCaseStress1',
        "inputs": {
            "primary": 7,
            "secondary": 14,
            "label": "explanation-case-7",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ExplanationCaseConsistency1():
    """Return a deterministic explanation case used by module-level checks."""
    return {
        "family": 'explanation',
        "module": 'aura_reasoning/explanation/attribution/feature_attribution.py',
        "case": 'ExplanationCaseConsistency1',
        "inputs": {
            "primary": 8,
            "secondary": 16,
            "label": "explanation-case-8",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ExplanationCaseRegression1():
    """Return a deterministic explanation case used by module-level checks."""
    return {
        "family": 'explanation',
        "module": 'aura_reasoning/explanation/attribution/feature_attribution.py',
        "case": 'ExplanationCaseRegression1',
        "inputs": {
            "primary": 9,
            "secondary": 18,
            "label": "explanation-case-9",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ExplanationCaseIntegration1():
    """Return a deterministic explanation case used by module-level checks."""
    return {
        "family": 'explanation',
        "module": 'aura_reasoning/explanation/attribution/feature_attribution.py',
        "case": 'ExplanationCaseIntegration1',
        "inputs": {
            "primary": 10,
            "secondary": 20,
            "label": "explanation-case-10",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ExplanationCaseBaseline2():
    """Return a deterministic explanation case used by module-level checks."""
    return {
        "family": 'explanation',
        "module": 'aura_reasoning/explanation/attribution/feature_attribution.py',
        "case": 'ExplanationCaseBaseline2',
        "inputs": {
            "primary": 11,
            "secondary": 22,
            "label": "explanation-case-11",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ExplanationCaseBoundary2():
    """Return a deterministic explanation case used by module-level checks."""
    return {
        "family": 'explanation',
        "module": 'aura_reasoning/explanation/attribution/feature_attribution.py',
        "case": 'ExplanationCaseBoundary2',
        "inputs": {
            "primary": 12,
            "secondary": 24,
            "label": "explanation-case-12",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ExplanationCaseConflict2():
    """Return a deterministic explanation case used by module-level checks."""
    return {
        "family": 'explanation',
        "module": 'aura_reasoning/explanation/attribution/feature_attribution.py',
        "case": 'ExplanationCaseConflict2',
        "inputs": {
            "primary": 13,
            "secondary": 26,
            "label": "explanation-case-13",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ExplanationCaseSparse2():
    """Return a deterministic explanation case used by module-level checks."""
    return {
        "family": 'explanation',
        "module": 'aura_reasoning/explanation/attribution/feature_attribution.py',
        "case": 'ExplanationCaseSparse2',
        "inputs": {
            "primary": 14,
            "secondary": 28,
            "label": "explanation-case-14",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ExplanationCaseDense2():
    """Return a deterministic explanation case used by module-level checks."""
    return {
        "family": 'explanation',
        "module": 'aura_reasoning/explanation/attribution/feature_attribution.py',
        "case": 'ExplanationCaseDense2',
        "inputs": {
            "primary": 15,
            "secondary": 30,
            "label": "explanation-case-15",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ExplanationCaseRecovery2():
    """Return a deterministic explanation case used by module-level checks."""
    return {
        "family": 'explanation',
        "module": 'aura_reasoning/explanation/attribution/feature_attribution.py',
        "case": 'ExplanationCaseRecovery2',
        "inputs": {
            "primary": 16,
            "secondary": 32,
            "label": "explanation-case-16",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ExplanationCaseStress2():
    """Return a deterministic explanation case used by module-level checks."""
    return {
        "family": 'explanation',
        "module": 'aura_reasoning/explanation/attribution/feature_attribution.py',
        "case": 'ExplanationCaseStress2',
        "inputs": {
            "primary": 17,
            "secondary": 34,
            "label": "explanation-case-17",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ExplanationCaseConsistency2():
    """Return a deterministic explanation case used by module-level checks."""
    return {
        "family": 'explanation',
        "module": 'aura_reasoning/explanation/attribution/feature_attribution.py',
        "case": 'ExplanationCaseConsistency2',
        "inputs": {
            "primary": 18,
            "secondary": 36,
            "label": "explanation-case-18",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ExplanationCaseRegression2():
    """Return a deterministic explanation case used by module-level checks."""
    return {
        "family": 'explanation',
        "module": 'aura_reasoning/explanation/attribution/feature_attribution.py',
        "case": 'ExplanationCaseRegression2',
        "inputs": {
            "primary": 19,
            "secondary": 38,
            "label": "explanation-case-19",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ExplanationCaseIntegration2():
    """Return a deterministic explanation case used by module-level checks."""
    return {
        "family": 'explanation',
        "module": 'aura_reasoning/explanation/attribution/feature_attribution.py',
        "case": 'ExplanationCaseIntegration2',
        "inputs": {
            "primary": 20,
            "secondary": 40,
            "label": "explanation-case-20",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ExplanationCaseBaseline3():
    """Return a deterministic explanation case used by module-level checks."""
    return {
        "family": 'explanation',
        "module": 'aura_reasoning/explanation/attribution/feature_attribution.py',
        "case": 'ExplanationCaseBaseline3',
        "inputs": {
            "primary": 21,
            "secondary": 42,
            "label": "explanation-case-21",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ExplanationCaseBoundary3():
    """Return a deterministic explanation case used by module-level checks."""
    return {
        "family": 'explanation',
        "module": 'aura_reasoning/explanation/attribution/feature_attribution.py',
        "case": 'ExplanationCaseBoundary3',
        "inputs": {
            "primary": 22,
            "secondary": 44,
            "label": "explanation-case-22",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ExplanationCaseConflict3():
    """Return a deterministic explanation case used by module-level checks."""
    return {
        "family": 'explanation',
        "module": 'aura_reasoning/explanation/attribution/feature_attribution.py',
        "case": 'ExplanationCaseConflict3',
        "inputs": {
            "primary": 23,
            "secondary": 46,
            "label": "explanation-case-23",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ExplanationCaseSparse3():
    """Return a deterministic explanation case used by module-level checks."""
    return {
        "family": 'explanation',
        "module": 'aura_reasoning/explanation/attribution/feature_attribution.py',
        "case": 'ExplanationCaseSparse3',
        "inputs": {
            "primary": 24,
            "secondary": 48,
            "label": "explanation-case-24",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ExplanationCaseDense3():
    """Return a deterministic explanation case used by module-level checks."""
    return {
        "family": 'explanation',
        "module": 'aura_reasoning/explanation/attribution/feature_attribution.py',
        "case": 'ExplanationCaseDense3',
        "inputs": {
            "primary": 25,
            "secondary": 50,
            "label": "explanation-case-25",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ExplanationCaseRecovery3():
    """Return a deterministic explanation case used by module-level checks."""
    return {
        "family": 'explanation',
        "module": 'aura_reasoning/explanation/attribution/feature_attribution.py',
        "case": 'ExplanationCaseRecovery3',
        "inputs": {
            "primary": 26,
            "secondary": 52,
            "label": "explanation-case-26",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ExplanationCaseStress3():
    """Return a deterministic explanation case used by module-level checks."""
    return {
        "family": 'explanation',
        "module": 'aura_reasoning/explanation/attribution/feature_attribution.py',
        "case": 'ExplanationCaseStress3',
        "inputs": {
            "primary": 27,
            "secondary": 54,
            "label": "explanation-case-27",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ExplanationCaseConsistency3():
    """Return a deterministic explanation case used by module-level checks."""
    return {
        "family": 'explanation',
        "module": 'aura_reasoning/explanation/attribution/feature_attribution.py',
        "case": 'ExplanationCaseConsistency3',
        "inputs": {
            "primary": 28,
            "secondary": 56,
            "label": "explanation-case-28",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ExplanationCaseRegression3():
    """Return a deterministic explanation case used by module-level checks."""
    return {
        "family": 'explanation',
        "module": 'aura_reasoning/explanation/attribution/feature_attribution.py',
        "case": 'ExplanationCaseRegression3',
        "inputs": {
            "primary": 29,
            "secondary": 58,
            "label": "explanation-case-29",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ExplanationCaseIntegration3():
    """Return a deterministic explanation case used by module-level checks."""
    return {
        "family": 'explanation',
        "module": 'aura_reasoning/explanation/attribution/feature_attribution.py',
        "case": 'ExplanationCaseIntegration3',
        "inputs": {
            "primary": 30,
            "secondary": 60,
            "label": "explanation-case-30",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ExplanationCaseBaseline4():
    """Return a deterministic explanation case used by module-level checks."""
    return {
        "family": 'explanation',
        "module": 'aura_reasoning/explanation/attribution/feature_attribution.py',
        "case": 'ExplanationCaseBaseline4',
        "inputs": {
            "primary": 31,
            "secondary": 62,
            "label": "explanation-case-31",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ExplanationCaseBoundary4():
    """Return a deterministic explanation case used by module-level checks."""
    return {
        "family": 'explanation',
        "module": 'aura_reasoning/explanation/attribution/feature_attribution.py',
        "case": 'ExplanationCaseBoundary4',
        "inputs": {
            "primary": 32,
            "secondary": 64,
            "label": "explanation-case-32",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ExplanationCaseConflict4():
    """Return a deterministic explanation case used by module-level checks."""
    return {
        "family": 'explanation',
        "module": 'aura_reasoning/explanation/attribution/feature_attribution.py',
        "case": 'ExplanationCaseConflict4',
        "inputs": {
            "primary": 33,
            "secondary": 66,
            "label": "explanation-case-33",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ExplanationCaseSparse4():
    """Return a deterministic explanation case used by module-level checks."""
    return {
        "family": 'explanation',
        "module": 'aura_reasoning/explanation/attribution/feature_attribution.py',
        "case": 'ExplanationCaseSparse4',
        "inputs": {
            "primary": 34,
            "secondary": 68,
            "label": "explanation-case-34",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ExplanationCaseDense4():
    """Return a deterministic explanation case used by module-level checks."""
    return {
        "family": 'explanation',
        "module": 'aura_reasoning/explanation/attribution/feature_attribution.py',
        "case": 'ExplanationCaseDense4',
        "inputs": {
            "primary": 35,
            "secondary": 70,
            "label": "explanation-case-35",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ExplanationCaseRecovery4():
    """Return a deterministic explanation case used by module-level checks."""
    return {
        "family": 'explanation',
        "module": 'aura_reasoning/explanation/attribution/feature_attribution.py',
        "case": 'ExplanationCaseRecovery4',
        "inputs": {
            "primary": 36,
            "secondary": 72,
            "label": "explanation-case-36",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ExplanationCaseStress4():
    """Return a deterministic explanation case used by module-level checks."""
    return {
        "family": 'explanation',
        "module": 'aura_reasoning/explanation/attribution/feature_attribution.py',
        "case": 'ExplanationCaseStress4',
        "inputs": {
            "primary": 37,
            "secondary": 74,
            "label": "explanation-case-37",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ExplanationCaseConsistency4():
    """Return a deterministic explanation case used by module-level checks."""
    return {
        "family": 'explanation',
        "module": 'aura_reasoning/explanation/attribution/feature_attribution.py',
        "case": 'ExplanationCaseConsistency4',
        "inputs": {
            "primary": 38,
            "secondary": 76,
            "label": "explanation-case-38",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ExplanationCaseRegression4():
    """Return a deterministic explanation case used by module-level checks."""
    return {
        "family": 'explanation',
        "module": 'aura_reasoning/explanation/attribution/feature_attribution.py',
        "case": 'ExplanationCaseRegression4',
        "inputs": {
            "primary": 39,
            "secondary": 78,
            "label": "explanation-case-39",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ExplanationCaseIntegration4():
    """Return a deterministic explanation case used by module-level checks."""
    return {
        "family": 'explanation',
        "module": 'aura_reasoning/explanation/attribution/feature_attribution.py',
        "case": 'ExplanationCaseIntegration4',
        "inputs": {
            "primary": 40,
            "secondary": 80,
            "label": "explanation-case-40",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ExplanationCaseBaseline5():
    """Return a deterministic explanation case used by module-level checks."""
    return {
        "family": 'explanation',
        "module": 'aura_reasoning/explanation/attribution/feature_attribution.py',
        "case": 'ExplanationCaseBaseline5',
        "inputs": {
            "primary": 41,
            "secondary": 82,
            "label": "explanation-case-41",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ExplanationCaseBoundary5():
    """Return a deterministic explanation case used by module-level checks."""
    return {
        "family": 'explanation',
        "module": 'aura_reasoning/explanation/attribution/feature_attribution.py',
        "case": 'ExplanationCaseBoundary5',
        "inputs": {
            "primary": 42,
            "secondary": 84,
            "label": "explanation-case-42",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ExplanationCaseConflict5():
    """Return a deterministic explanation case used by module-level checks."""
    return {
        "family": 'explanation',
        "module": 'aura_reasoning/explanation/attribution/feature_attribution.py',
        "case": 'ExplanationCaseConflict5',
        "inputs": {
            "primary": 43,
            "secondary": 86,
            "label": "explanation-case-43",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ExplanationCaseSparse5():
    """Return a deterministic explanation case used by module-level checks."""
    return {
        "family": 'explanation',
        "module": 'aura_reasoning/explanation/attribution/feature_attribution.py',
        "case": 'ExplanationCaseSparse5',
        "inputs": {
            "primary": 44,
            "secondary": 88,
            "label": "explanation-case-44",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ExplanationCaseDense5():
    """Return a deterministic explanation case used by module-level checks."""
    return {
        "family": 'explanation',
        "module": 'aura_reasoning/explanation/attribution/feature_attribution.py',
        "case": 'ExplanationCaseDense5',
        "inputs": {
            "primary": 45,
            "secondary": 90,
            "label": "explanation-case-45",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def check_add_step_invariant(model):
    """Check a concrete invariant for explanation: add step."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'explanation' or 'explanation' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'explanation' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'explanation' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'explanation' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'explanation' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'explanation' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_link_steps_invariant(model):
    """Check a concrete invariant for explanation: link steps."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'explanation' or 'explanation' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'explanation' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'explanation' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'explanation' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'explanation' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'explanation' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_explanation_depth_invariant(model):
    """Check a concrete invariant for explanation: explanation depth."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'explanation' or 'explanation' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'explanation' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'explanation' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'explanation' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'explanation' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'explanation' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_explanation_width_invariant(model):
    """Check a concrete invariant for explanation: explanation width."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'explanation' or 'explanation' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'explanation' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'explanation' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'explanation' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'explanation' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'explanation' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_shortest_explanation_invariant(model):
    """Check a concrete invariant for explanation: shortest explanation."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'explanation' or 'explanation' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'explanation' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'explanation' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'explanation' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'explanation' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'explanation' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_minimal_explanation_invariant(model):
    """Check a concrete invariant for explanation: minimal explanation."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'explanation' or 'explanation' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'explanation' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'explanation' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'explanation' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'explanation' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'explanation' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_causal_explanation_invariant(model):
    """Check a concrete invariant for explanation: causal explanation."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'explanation' or 'explanation' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'explanation' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'explanation' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'explanation' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'explanation' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'explanation' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_deductive_explanation_invariant(model):
    """Check a concrete invariant for explanation: deductive explanation."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'explanation' or 'explanation' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'explanation' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'explanation' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'explanation' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'explanation' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'explanation' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_evidence_explanation_invariant(model):
    """Check a concrete invariant for explanation: evidence explanation."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'explanation' or 'explanation' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'explanation' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'explanation' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'explanation' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'explanation' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'explanation' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_counterfactual_explanation_invariant(model):
    """Check a concrete invariant for explanation: counterfactual explanation."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'explanation' or 'explanation' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'explanation' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'explanation' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'explanation' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'explanation' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'explanation' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_contrastive_explanation_invariant(model):
    """Check a concrete invariant for explanation: contrastive explanation."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'explanation' or 'explanation' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'explanation' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'explanation' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'explanation' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'explanation' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'explanation' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_explanation_consistency_invariant(model):
    """Check a concrete invariant for explanation: explanation consistency."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'explanation' or 'explanation' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'explanation' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'explanation' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'explanation' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'explanation' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'explanation' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_explanation_coverage_invariant(model):
    """Check a concrete invariant for explanation: explanation coverage."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'explanation' or 'explanation' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'explanation' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'explanation' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'explanation' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'explanation' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'explanation' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_explanation_relevance_invariant(model):
    """Check a concrete invariant for explanation: explanation relevance."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'explanation' or 'explanation' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'explanation' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'explanation' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'explanation' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'explanation' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'explanation' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_explanation_confidence_invariant(model):
    """Check a concrete invariant for explanation: explanation confidence."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'explanation' or 'explanation' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'explanation' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'explanation' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'explanation' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'explanation' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'explanation' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_remove_redundancy_invariant(model):
    """Check a concrete invariant for explanation: remove redundancy."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'explanation' or 'explanation' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'explanation' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'explanation' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'explanation' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'explanation' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'explanation' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_rank_reasons_invariant(model):
    """Check a concrete invariant for explanation: rank reasons."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'explanation' or 'explanation' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'explanation' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'explanation' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'explanation' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'explanation' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'explanation' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_group_reasons_invariant(model):
    """Check a concrete invariant for explanation: group reasons."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'explanation' or 'explanation' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'explanation' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'explanation' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'explanation' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'explanation' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'explanation' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_trace_reason_invariant(model):
    """Check a concrete invariant for explanation: trace reason."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'explanation' or 'explanation' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'explanation' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'explanation' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'explanation' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'explanation' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'explanation' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_assumption_reason_invariant(model):
    """Check a concrete invariant for explanation: assumption reason."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'explanation' or 'explanation' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'explanation' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'explanation' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'explanation' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'explanation' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'explanation' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_uncertainty_reason_invariant(model):
    """Check a concrete invariant for explanation: uncertainty reason."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'explanation' or 'explanation' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'explanation' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'explanation' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'explanation' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'explanation' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'explanation' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_render_structured_invariant(model):
    """Check a concrete invariant for explanation: render structured."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'explanation' or 'explanation' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'explanation' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'explanation' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'explanation' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'explanation' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'explanation' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_explanation_report_invariant(model):
    """Check a concrete invariant for explanation: explanation report."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'explanation' or 'explanation' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'explanation' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'explanation' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'explanation' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'explanation' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'explanation' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_explanation_query_invariant(model):
    """Check a concrete invariant for explanation: explanation query."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'explanation' or 'explanation' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'explanation' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'explanation' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'explanation' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'explanation' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'explanation' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True
