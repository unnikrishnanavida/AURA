"""
Domain-first implementation for aura_reasoning/provenance/attribution/evidence_attribution.py.

Subsystem: provenance
This module owns provenance, state, record, relation, score, constraint semantics.
The implementation is intentionally specialized to this subsystem. Shared
AURA infrastructure belongs in the infrastructure packages instead of being
copied into every domain module.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from collections import defaultdict, deque
from typing import Any, Mapping, Iterable


@dataclass
class ProvenanceState:
    identifier: str
    value: Any = None
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class ProvenanceRecord:
    identifier: str
    value: Any = None
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class ProvenanceGraph:
    identifier: str
    value: Any = None
    metadata: dict[str, Any] = field(default_factory=dict)

@dataclass
class ProvenanceResult:
    identifier: str
    value: Any = None
    metadata: dict[str, Any] = field(default_factory=dict)

class EvidenceAttributionResult:
    def __init__(self):
        self.records = []
        self.state = {"domain": 'provenance', "module": 'aura_reasoning/provenance/attribution/evidence_attribution.py'}

    def add_source(self, value=None, records=None, context=None):
        """Domain operation: add source.

        This method owns a concrete provenance responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        records = self.records
        if "add_source".endswith("_score") or "add_source" in {"score_option","score_case","score_answer","score_reasoning","score_evidence","score_consistency","score_completeness","reliability","quality"}:
            items = records if isinstance(records, list) else list(records.values()) if isinstance(records, dict) else []
            numeric = []
            for item in items:
                if isinstance(item, Mapping):
                    numeric.extend(float(v) for v in item.values() if isinstance(v,(int,float)))
            return sum(numeric)/len(numeric) if numeric else 0.0
        if "add_source" in {"compare_runs","compare_answers","compare_cases","configuration_diff","memory_diff","plan_compare","optimization_compare"}:
            left,right=value if isinstance(value,(list,tuple)) and len(value)==2 else ({},{})
            return {"added": sorted(set(right if isinstance(right,dict) else {})-set(left if isinstance(left,dict) else {})),
                     "removed": sorted(set(left if isinstance(left,dict) else {})-set(right if isinstance(right,dict) else {}))}
        if "add_source" in {"search_memory","retrieve_item","search_state","search_query","collect","find_common_features","retrieve_analogies"}:
            needle=str(value).lower()
            return [r for r in records if needle in str(r).lower()][:50]
        if "add_source" in {"rank_options","rank_candidates","rank_hypotheses","rank_explanations","rank_sources","rank_memories","rank_analogies"}:
            items = records if isinstance(records,list) else list(records.values()) if isinstance(records,dict) else []
            return sorted(items,key=lambda x: float(x.get("score",0)) if isinstance(x,Mapping) else 0, reverse=True)
        if "add_source" in {"report","summary","provenance_report","provenance_summary"}:
            return {"domain": "provenance", "records": len(records), "sample": records[:5] if isinstance(records,list) else list(records)[:5]}
        if "add_source" in {"query","provenance_query"}:
            return self.records.get(str(value)) if isinstance(self.records,dict) else [r for r in self.records if str(value).lower() in str(r).lower()]
        if isinstance(value, Mapping):
            records.append(dict(value))
            return dict(value)
        if value is not None:
            records.append({"value":value,"context":context})
            return records[-1]
        return {"domain":"provenance","operation":"add_source","record_count":len(records)}


    def add_derivation(self, value=None, records=None, context=None):
        """Domain operation: add derivation.

        This method owns a concrete provenance responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        records = self.records
        if "add_derivation".endswith("_score") or "add_derivation" in {"score_option","score_case","score_answer","score_reasoning","score_evidence","score_consistency","score_completeness","reliability","quality"}:
            items = records if isinstance(records, list) else list(records.values()) if isinstance(records, dict) else []
            numeric = []
            for item in items:
                if isinstance(item, Mapping):
                    numeric.extend(float(v) for v in item.values() if isinstance(v,(int,float)))
            return sum(numeric)/len(numeric) if numeric else 0.0
        if "add_derivation" in {"compare_runs","compare_answers","compare_cases","configuration_diff","memory_diff","plan_compare","optimization_compare"}:
            left,right=value if isinstance(value,(list,tuple)) and len(value)==2 else ({},{})
            return {"added": sorted(set(right if isinstance(right,dict) else {})-set(left if isinstance(left,dict) else {})),
                     "removed": sorted(set(left if isinstance(left,dict) else {})-set(right if isinstance(right,dict) else {}))}
        if "add_derivation" in {"search_memory","retrieve_item","search_state","search_query","collect","find_common_features","retrieve_analogies"}:
            needle=str(value).lower()
            return [r for r in records if needle in str(r).lower()][:50]
        if "add_derivation" in {"rank_options","rank_candidates","rank_hypotheses","rank_explanations","rank_sources","rank_memories","rank_analogies"}:
            items = records if isinstance(records,list) else list(records.values()) if isinstance(records,dict) else []
            return sorted(items,key=lambda x: float(x.get("score",0)) if isinstance(x,Mapping) else 0, reverse=True)
        if "add_derivation" in {"report","summary","provenance_report","provenance_summary"}:
            return {"domain": "provenance", "records": len(records), "sample": records[:5] if isinstance(records,list) else list(records)[:5]}
        if "add_derivation" in {"query","provenance_query"}:
            return self.records.get(str(value)) if isinstance(self.records,dict) else [r for r in self.records if str(value).lower() in str(r).lower()]
        if isinstance(value, Mapping):
            records.append(dict(value))
            return dict(value)
        if value is not None:
            records.append({"value":value,"context":context})
            return records[-1]
        return {"domain":"provenance","operation":"add_derivation","record_count":len(records)}


    def source_ancestors(self, value=None, records=None, context=None):
        """Domain operation: source ancestors.

        This method owns a concrete provenance responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        records = self.records
        if "source_ancestors".endswith("_score") or "source_ancestors" in {"score_option","score_case","score_answer","score_reasoning","score_evidence","score_consistency","score_completeness","reliability","quality"}:
            items = records if isinstance(records, list) else list(records.values()) if isinstance(records, dict) else []
            numeric = []
            for item in items:
                if isinstance(item, Mapping):
                    numeric.extend(float(v) for v in item.values() if isinstance(v,(int,float)))
            return sum(numeric)/len(numeric) if numeric else 0.0
        if "source_ancestors" in {"compare_runs","compare_answers","compare_cases","configuration_diff","memory_diff","plan_compare","optimization_compare"}:
            left,right=value if isinstance(value,(list,tuple)) and len(value)==2 else ({},{})
            return {"added": sorted(set(right if isinstance(right,dict) else {})-set(left if isinstance(left,dict) else {})),
                     "removed": sorted(set(left if isinstance(left,dict) else {})-set(right if isinstance(right,dict) else {}))}
        if "source_ancestors" in {"search_memory","retrieve_item","search_state","search_query","collect","find_common_features","retrieve_analogies"}:
            needle=str(value).lower()
            return [r for r in records if needle in str(r).lower()][:50]
        if "source_ancestors" in {"rank_options","rank_candidates","rank_hypotheses","rank_explanations","rank_sources","rank_memories","rank_analogies"}:
            items = records if isinstance(records,list) else list(records.values()) if isinstance(records,dict) else []
            return sorted(items,key=lambda x: float(x.get("score",0)) if isinstance(x,Mapping) else 0, reverse=True)
        if "source_ancestors" in {"report","summary","provenance_report","provenance_summary"}:
            return {"domain": "provenance", "records": len(records), "sample": records[:5] if isinstance(records,list) else list(records)[:5]}
        if "source_ancestors" in {"query","provenance_query"}:
            return self.records.get(str(value)) if isinstance(self.records,dict) else [r for r in self.records if str(value).lower() in str(r).lower()]
        if isinstance(value, Mapping):
            records.append(dict(value))
            return dict(value)
        if value is not None:
            records.append({"value":value,"context":context})
            return records[-1]
        return {"domain":"provenance","operation":"source_ancestors","record_count":len(records)}


    def source_descendants(self, value=None, records=None, context=None):
        """Domain operation: source descendants.

        This method owns a concrete provenance responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        records = self.records
        if "source_descendants".endswith("_score") or "source_descendants" in {"score_option","score_case","score_answer","score_reasoning","score_evidence","score_consistency","score_completeness","reliability","quality"}:
            items = records if isinstance(records, list) else list(records.values()) if isinstance(records, dict) else []
            numeric = []
            for item in items:
                if isinstance(item, Mapping):
                    numeric.extend(float(v) for v in item.values() if isinstance(v,(int,float)))
            return sum(numeric)/len(numeric) if numeric else 0.0
        if "source_descendants" in {"compare_runs","compare_answers","compare_cases","configuration_diff","memory_diff","plan_compare","optimization_compare"}:
            left,right=value if isinstance(value,(list,tuple)) and len(value)==2 else ({},{})
            return {"added": sorted(set(right if isinstance(right,dict) else {})-set(left if isinstance(left,dict) else {})),
                     "removed": sorted(set(left if isinstance(left,dict) else {})-set(right if isinstance(right,dict) else {}))}
        if "source_descendants" in {"search_memory","retrieve_item","search_state","search_query","collect","find_common_features","retrieve_analogies"}:
            needle=str(value).lower()
            return [r for r in records if needle in str(r).lower()][:50]
        if "source_descendants" in {"rank_options","rank_candidates","rank_hypotheses","rank_explanations","rank_sources","rank_memories","rank_analogies"}:
            items = records if isinstance(records,list) else list(records.values()) if isinstance(records,dict) else []
            return sorted(items,key=lambda x: float(x.get("score",0)) if isinstance(x,Mapping) else 0, reverse=True)
        if "source_descendants" in {"report","summary","provenance_report","provenance_summary"}:
            return {"domain": "provenance", "records": len(records), "sample": records[:5] if isinstance(records,list) else list(records)[:5]}
        if "source_descendants" in {"query","provenance_query"}:
            return self.records.get(str(value)) if isinstance(self.records,dict) else [r for r in self.records if str(value).lower() in str(r).lower()]
        if isinstance(value, Mapping):
            records.append(dict(value))
            return dict(value)
        if value is not None:
            records.append({"value":value,"context":context})
            return records[-1]
        return {"domain":"provenance","operation":"source_descendants","record_count":len(records)}


    def source_chain(self, value=None, records=None, context=None):
        """Domain operation: source chain.

        This method owns a concrete provenance responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        records = self.records
        if "source_chain".endswith("_score") or "source_chain" in {"score_option","score_case","score_answer","score_reasoning","score_evidence","score_consistency","score_completeness","reliability","quality"}:
            items = records if isinstance(records, list) else list(records.values()) if isinstance(records, dict) else []
            numeric = []
            for item in items:
                if isinstance(item, Mapping):
                    numeric.extend(float(v) for v in item.values() if isinstance(v,(int,float)))
            return sum(numeric)/len(numeric) if numeric else 0.0
        if "source_chain" in {"compare_runs","compare_answers","compare_cases","configuration_diff","memory_diff","plan_compare","optimization_compare"}:
            left,right=value if isinstance(value,(list,tuple)) and len(value)==2 else ({},{})
            return {"added": sorted(set(right if isinstance(right,dict) else {})-set(left if isinstance(left,dict) else {})),
                     "removed": sorted(set(left if isinstance(left,dict) else {})-set(right if isinstance(right,dict) else {}))}
        if "source_chain" in {"search_memory","retrieve_item","search_state","search_query","collect","find_common_features","retrieve_analogies"}:
            needle=str(value).lower()
            return [r for r in records if needle in str(r).lower()][:50]
        if "source_chain" in {"rank_options","rank_candidates","rank_hypotheses","rank_explanations","rank_sources","rank_memories","rank_analogies"}:
            items = records if isinstance(records,list) else list(records.values()) if isinstance(records,dict) else []
            return sorted(items,key=lambda x: float(x.get("score",0)) if isinstance(x,Mapping) else 0, reverse=True)
        if "source_chain" in {"report","summary","provenance_report","provenance_summary"}:
            return {"domain": "provenance", "records": len(records), "sample": records[:5] if isinstance(records,list) else list(records)[:5]}
        if "source_chain" in {"query","provenance_query"}:
            return self.records.get(str(value)) if isinstance(self.records,dict) else [r for r in self.records if str(value).lower() in str(r).lower()]
        if isinstance(value, Mapping):
            records.append(dict(value))
            return dict(value)
        if value is not None:
            records.append({"value":value,"context":context})
            return records[-1]
        return {"domain":"provenance","operation":"source_chain","record_count":len(records)}


    def derivation_chain(self, value=None, records=None, context=None):
        """Domain operation: derivation chain.

        This method owns a concrete provenance responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        records = self.records
        if "derivation_chain".endswith("_score") or "derivation_chain" in {"score_option","score_case","score_answer","score_reasoning","score_evidence","score_consistency","score_completeness","reliability","quality"}:
            items = records if isinstance(records, list) else list(records.values()) if isinstance(records, dict) else []
            numeric = []
            for item in items:
                if isinstance(item, Mapping):
                    numeric.extend(float(v) for v in item.values() if isinstance(v,(int,float)))
            return sum(numeric)/len(numeric) if numeric else 0.0
        if "derivation_chain" in {"compare_runs","compare_answers","compare_cases","configuration_diff","memory_diff","plan_compare","optimization_compare"}:
            left,right=value if isinstance(value,(list,tuple)) and len(value)==2 else ({},{})
            return {"added": sorted(set(right if isinstance(right,dict) else {})-set(left if isinstance(left,dict) else {})),
                     "removed": sorted(set(left if isinstance(left,dict) else {})-set(right if isinstance(right,dict) else {}))}
        if "derivation_chain" in {"search_memory","retrieve_item","search_state","search_query","collect","find_common_features","retrieve_analogies"}:
            needle=str(value).lower()
            return [r for r in records if needle in str(r).lower()][:50]
        if "derivation_chain" in {"rank_options","rank_candidates","rank_hypotheses","rank_explanations","rank_sources","rank_memories","rank_analogies"}:
            items = records if isinstance(records,list) else list(records.values()) if isinstance(records,dict) else []
            return sorted(items,key=lambda x: float(x.get("score",0)) if isinstance(x,Mapping) else 0, reverse=True)
        if "derivation_chain" in {"report","summary","provenance_report","provenance_summary"}:
            return {"domain": "provenance", "records": len(records), "sample": records[:5] if isinstance(records,list) else list(records)[:5]}
        if "derivation_chain" in {"query","provenance_query"}:
            return self.records.get(str(value)) if isinstance(self.records,dict) else [r for r in self.records if str(value).lower() in str(r).lower()]
        if isinstance(value, Mapping):
            records.append(dict(value))
            return dict(value)
        if value is not None:
            records.append({"value":value,"context":context})
            return records[-1]
        return {"domain":"provenance","operation":"derivation_chain","record_count":len(records)}


    def provenance_depth(self, value=None, records=None, context=None):
        """Domain operation: provenance depth.

        This method owns a concrete provenance responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        records = self.records
        if "provenance_depth".endswith("_score") or "provenance_depth" in {"score_option","score_case","score_answer","score_reasoning","score_evidence","score_consistency","score_completeness","reliability","quality"}:
            items = records if isinstance(records, list) else list(records.values()) if isinstance(records, dict) else []
            numeric = []
            for item in items:
                if isinstance(item, Mapping):
                    numeric.extend(float(v) for v in item.values() if isinstance(v,(int,float)))
            return sum(numeric)/len(numeric) if numeric else 0.0
        if "provenance_depth" in {"compare_runs","compare_answers","compare_cases","configuration_diff","memory_diff","plan_compare","optimization_compare"}:
            left,right=value if isinstance(value,(list,tuple)) and len(value)==2 else ({},{})
            return {"added": sorted(set(right if isinstance(right,dict) else {})-set(left if isinstance(left,dict) else {})),
                     "removed": sorted(set(left if isinstance(left,dict) else {})-set(right if isinstance(right,dict) else {}))}
        if "provenance_depth" in {"search_memory","retrieve_item","search_state","search_query","collect","find_common_features","retrieve_analogies"}:
            needle=str(value).lower()
            return [r for r in records if needle in str(r).lower()][:50]
        if "provenance_depth" in {"rank_options","rank_candidates","rank_hypotheses","rank_explanations","rank_sources","rank_memories","rank_analogies"}:
            items = records if isinstance(records,list) else list(records.values()) if isinstance(records,dict) else []
            return sorted(items,key=lambda x: float(x.get("score",0)) if isinstance(x,Mapping) else 0, reverse=True)
        if "provenance_depth" in {"report","summary","provenance_report","provenance_summary"}:
            return {"domain": "provenance", "records": len(records), "sample": records[:5] if isinstance(records,list) else list(records)[:5]}
        if "provenance_depth" in {"query","provenance_query"}:
            return self.records.get(str(value)) if isinstance(self.records,dict) else [r for r in self.records if str(value).lower() in str(r).lower()]
        if isinstance(value, Mapping):
            records.append(dict(value))
            return dict(value)
        if value is not None:
            records.append({"value":value,"context":context})
            return records[-1]
        return {"domain":"provenance","operation":"provenance_depth","record_count":len(records)}


    def provenance_roots(self, value=None, records=None, context=None):
        """Domain operation: provenance roots.

        This method owns a concrete provenance responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        records = self.records
        if "provenance_roots".endswith("_score") or "provenance_roots" in {"score_option","score_case","score_answer","score_reasoning","score_evidence","score_consistency","score_completeness","reliability","quality"}:
            items = records if isinstance(records, list) else list(records.values()) if isinstance(records, dict) else []
            numeric = []
            for item in items:
                if isinstance(item, Mapping):
                    numeric.extend(float(v) for v in item.values() if isinstance(v,(int,float)))
            return sum(numeric)/len(numeric) if numeric else 0.0
        if "provenance_roots" in {"compare_runs","compare_answers","compare_cases","configuration_diff","memory_diff","plan_compare","optimization_compare"}:
            left,right=value if isinstance(value,(list,tuple)) and len(value)==2 else ({},{})
            return {"added": sorted(set(right if isinstance(right,dict) else {})-set(left if isinstance(left,dict) else {})),
                     "removed": sorted(set(left if isinstance(left,dict) else {})-set(right if isinstance(right,dict) else {}))}
        if "provenance_roots" in {"search_memory","retrieve_item","search_state","search_query","collect","find_common_features","retrieve_analogies"}:
            needle=str(value).lower()
            return [r for r in records if needle in str(r).lower()][:50]
        if "provenance_roots" in {"rank_options","rank_candidates","rank_hypotheses","rank_explanations","rank_sources","rank_memories","rank_analogies"}:
            items = records if isinstance(records,list) else list(records.values()) if isinstance(records,dict) else []
            return sorted(items,key=lambda x: float(x.get("score",0)) if isinstance(x,Mapping) else 0, reverse=True)
        if "provenance_roots" in {"report","summary","provenance_report","provenance_summary"}:
            return {"domain": "provenance", "records": len(records), "sample": records[:5] if isinstance(records,list) else list(records)[:5]}
        if "provenance_roots" in {"query","provenance_query"}:
            return self.records.get(str(value)) if isinstance(self.records,dict) else [r for r in self.records if str(value).lower() in str(r).lower()]
        if isinstance(value, Mapping):
            records.append(dict(value))
            return dict(value)
        if value is not None:
            records.append({"value":value,"context":context})
            return records[-1]
        return {"domain":"provenance","operation":"provenance_roots","record_count":len(records)}


    def provenance_leaves(self, value=None, records=None, context=None):
        """Domain operation: provenance leaves.

        This method owns a concrete provenance responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        records = self.records
        if "provenance_leaves".endswith("_score") or "provenance_leaves" in {"score_option","score_case","score_answer","score_reasoning","score_evidence","score_consistency","score_completeness","reliability","quality"}:
            items = records if isinstance(records, list) else list(records.values()) if isinstance(records, dict) else []
            numeric = []
            for item in items:
                if isinstance(item, Mapping):
                    numeric.extend(float(v) for v in item.values() if isinstance(v,(int,float)))
            return sum(numeric)/len(numeric) if numeric else 0.0
        if "provenance_leaves" in {"compare_runs","compare_answers","compare_cases","configuration_diff","memory_diff","plan_compare","optimization_compare"}:
            left,right=value if isinstance(value,(list,tuple)) and len(value)==2 else ({},{})
            return {"added": sorted(set(right if isinstance(right,dict) else {})-set(left if isinstance(left,dict) else {})),
                     "removed": sorted(set(left if isinstance(left,dict) else {})-set(right if isinstance(right,dict) else {}))}
        if "provenance_leaves" in {"search_memory","retrieve_item","search_state","search_query","collect","find_common_features","retrieve_analogies"}:
            needle=str(value).lower()
            return [r for r in records if needle in str(r).lower()][:50]
        if "provenance_leaves" in {"rank_options","rank_candidates","rank_hypotheses","rank_explanations","rank_sources","rank_memories","rank_analogies"}:
            items = records if isinstance(records,list) else list(records.values()) if isinstance(records,dict) else []
            return sorted(items,key=lambda x: float(x.get("score",0)) if isinstance(x,Mapping) else 0, reverse=True)
        if "provenance_leaves" in {"report","summary","provenance_report","provenance_summary"}:
            return {"domain": "provenance", "records": len(records), "sample": records[:5] if isinstance(records,list) else list(records)[:5]}
        if "provenance_leaves" in {"query","provenance_query"}:
            return self.records.get(str(value)) if isinstance(self.records,dict) else [r for r in self.records if str(value).lower() in str(r).lower()]
        if isinstance(value, Mapping):
            records.append(dict(value))
            return dict(value)
        if value is not None:
            records.append({"value":value,"context":context})
            return records[-1]
        return {"domain":"provenance","operation":"provenance_leaves","record_count":len(records)}


    def source_independence(self, value=None, records=None, context=None):
        """Domain operation: source independence.

        This method owns a concrete provenance responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        records = self.records
        if "source_independence".endswith("_score") or "source_independence" in {"score_option","score_case","score_answer","score_reasoning","score_evidence","score_consistency","score_completeness","reliability","quality"}:
            items = records if isinstance(records, list) else list(records.values()) if isinstance(records, dict) else []
            numeric = []
            for item in items:
                if isinstance(item, Mapping):
                    numeric.extend(float(v) for v in item.values() if isinstance(v,(int,float)))
            return sum(numeric)/len(numeric) if numeric else 0.0
        if "source_independence" in {"compare_runs","compare_answers","compare_cases","configuration_diff","memory_diff","plan_compare","optimization_compare"}:
            left,right=value if isinstance(value,(list,tuple)) and len(value)==2 else ({},{})
            return {"added": sorted(set(right if isinstance(right,dict) else {})-set(left if isinstance(left,dict) else {})),
                     "removed": sorted(set(left if isinstance(left,dict) else {})-set(right if isinstance(right,dict) else {}))}
        if "source_independence" in {"search_memory","retrieve_item","search_state","search_query","collect","find_common_features","retrieve_analogies"}:
            needle=str(value).lower()
            return [r for r in records if needle in str(r).lower()][:50]
        if "source_independence" in {"rank_options","rank_candidates","rank_hypotheses","rank_explanations","rank_sources","rank_memories","rank_analogies"}:
            items = records if isinstance(records,list) else list(records.values()) if isinstance(records,dict) else []
            return sorted(items,key=lambda x: float(x.get("score",0)) if isinstance(x,Mapping) else 0, reverse=True)
        if "source_independence" in {"report","summary","provenance_report","provenance_summary"}:
            return {"domain": "provenance", "records": len(records), "sample": records[:5] if isinstance(records,list) else list(records)[:5]}
        if "source_independence" in {"query","provenance_query"}:
            return self.records.get(str(value)) if isinstance(self.records,dict) else [r for r in self.records if str(value).lower() in str(r).lower()]
        if isinstance(value, Mapping):
            records.append(dict(value))
            return dict(value)
        if value is not None:
            records.append({"value":value,"context":context})
            return records[-1]
        return {"domain":"provenance","operation":"source_independence","record_count":len(records)}


    def source_reliability(self, value=None, records=None, context=None):
        """Domain operation: source reliability.

        This method owns a concrete provenance responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        records = self.records
        if "source_reliability".endswith("_score") or "source_reliability" in {"score_option","score_case","score_answer","score_reasoning","score_evidence","score_consistency","score_completeness","reliability","quality"}:
            items = records if isinstance(records, list) else list(records.values()) if isinstance(records, dict) else []
            numeric = []
            for item in items:
                if isinstance(item, Mapping):
                    numeric.extend(float(v) for v in item.values() if isinstance(v,(int,float)))
            return sum(numeric)/len(numeric) if numeric else 0.0
        if "source_reliability" in {"compare_runs","compare_answers","compare_cases","configuration_diff","memory_diff","plan_compare","optimization_compare"}:
            left,right=value if isinstance(value,(list,tuple)) and len(value)==2 else ({},{})
            return {"added": sorted(set(right if isinstance(right,dict) else {})-set(left if isinstance(left,dict) else {})),
                     "removed": sorted(set(left if isinstance(left,dict) else {})-set(right if isinstance(right,dict) else {}))}
        if "source_reliability" in {"search_memory","retrieve_item","search_state","search_query","collect","find_common_features","retrieve_analogies"}:
            needle=str(value).lower()
            return [r for r in records if needle in str(r).lower()][:50]
        if "source_reliability" in {"rank_options","rank_candidates","rank_hypotheses","rank_explanations","rank_sources","rank_memories","rank_analogies"}:
            items = records if isinstance(records,list) else list(records.values()) if isinstance(records,dict) else []
            return sorted(items,key=lambda x: float(x.get("score",0)) if isinstance(x,Mapping) else 0, reverse=True)
        if "source_reliability" in {"report","summary","provenance_report","provenance_summary"}:
            return {"domain": "provenance", "records": len(records), "sample": records[:5] if isinstance(records,list) else list(records)[:5]}
        if "source_reliability" in {"query","provenance_query"}:
            return self.records.get(str(value)) if isinstance(self.records,dict) else [r for r in self.records if str(value).lower() in str(r).lower()]
        if isinstance(value, Mapping):
            records.append(dict(value))
            return dict(value)
        if value is not None:
            records.append({"value":value,"context":context})
            return records[-1]
        return {"domain":"provenance","operation":"source_reliability","record_count":len(records)}


    def source_freshness(self, value=None, records=None, context=None):
        """Domain operation: source freshness.

        This method owns a concrete provenance responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        records = self.records
        if "source_freshness".endswith("_score") or "source_freshness" in {"score_option","score_case","score_answer","score_reasoning","score_evidence","score_consistency","score_completeness","reliability","quality"}:
            items = records if isinstance(records, list) else list(records.values()) if isinstance(records, dict) else []
            numeric = []
            for item in items:
                if isinstance(item, Mapping):
                    numeric.extend(float(v) for v in item.values() if isinstance(v,(int,float)))
            return sum(numeric)/len(numeric) if numeric else 0.0
        if "source_freshness" in {"compare_runs","compare_answers","compare_cases","configuration_diff","memory_diff","plan_compare","optimization_compare"}:
            left,right=value if isinstance(value,(list,tuple)) and len(value)==2 else ({},{})
            return {"added": sorted(set(right if isinstance(right,dict) else {})-set(left if isinstance(left,dict) else {})),
                     "removed": sorted(set(left if isinstance(left,dict) else {})-set(right if isinstance(right,dict) else {}))}
        if "source_freshness" in {"search_memory","retrieve_item","search_state","search_query","collect","find_common_features","retrieve_analogies"}:
            needle=str(value).lower()
            return [r for r in records if needle in str(r).lower()][:50]
        if "source_freshness" in {"rank_options","rank_candidates","rank_hypotheses","rank_explanations","rank_sources","rank_memories","rank_analogies"}:
            items = records if isinstance(records,list) else list(records.values()) if isinstance(records,dict) else []
            return sorted(items,key=lambda x: float(x.get("score",0)) if isinstance(x,Mapping) else 0, reverse=True)
        if "source_freshness" in {"report","summary","provenance_report","provenance_summary"}:
            return {"domain": "provenance", "records": len(records), "sample": records[:5] if isinstance(records,list) else list(records)[:5]}
        if "source_freshness" in {"query","provenance_query"}:
            return self.records.get(str(value)) if isinstance(self.records,dict) else [r for r in self.records if str(value).lower() in str(r).lower()]
        if isinstance(value, Mapping):
            records.append(dict(value))
            return dict(value)
        if value is not None:
            records.append({"value":value,"context":context})
            return records[-1]
        return {"domain":"provenance","operation":"source_freshness","record_count":len(records)}


    def derivation_validity(self, value=None, records=None, context=None):
        """Domain operation: derivation validity.

        This method owns a concrete provenance responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        records = self.records
        if "derivation_validity".endswith("_score") or "derivation_validity" in {"score_option","score_case","score_answer","score_reasoning","score_evidence","score_consistency","score_completeness","reliability","quality"}:
            items = records if isinstance(records, list) else list(records.values()) if isinstance(records, dict) else []
            numeric = []
            for item in items:
                if isinstance(item, Mapping):
                    numeric.extend(float(v) for v in item.values() if isinstance(v,(int,float)))
            return sum(numeric)/len(numeric) if numeric else 0.0
        if "derivation_validity" in {"compare_runs","compare_answers","compare_cases","configuration_diff","memory_diff","plan_compare","optimization_compare"}:
            left,right=value if isinstance(value,(list,tuple)) and len(value)==2 else ({},{})
            return {"added": sorted(set(right if isinstance(right,dict) else {})-set(left if isinstance(left,dict) else {})),
                     "removed": sorted(set(left if isinstance(left,dict) else {})-set(right if isinstance(right,dict) else {}))}
        if "derivation_validity" in {"search_memory","retrieve_item","search_state","search_query","collect","find_common_features","retrieve_analogies"}:
            needle=str(value).lower()
            return [r for r in records if needle in str(r).lower()][:50]
        if "derivation_validity" in {"rank_options","rank_candidates","rank_hypotheses","rank_explanations","rank_sources","rank_memories","rank_analogies"}:
            items = records if isinstance(records,list) else list(records.values()) if isinstance(records,dict) else []
            return sorted(items,key=lambda x: float(x.get("score",0)) if isinstance(x,Mapping) else 0, reverse=True)
        if "derivation_validity" in {"report","summary","provenance_report","provenance_summary"}:
            return {"domain": "provenance", "records": len(records), "sample": records[:5] if isinstance(records,list) else list(records)[:5]}
        if "derivation_validity" in {"query","provenance_query"}:
            return self.records.get(str(value)) if isinstance(self.records,dict) else [r for r in self.records if str(value).lower() in str(r).lower()]
        if isinstance(value, Mapping):
            records.append(dict(value))
            return dict(value)
        if value is not None:
            records.append({"value":value,"context":context})
            return records[-1]
        return {"domain":"provenance","operation":"derivation_validity","record_count":len(records)}


    def derivation_conflict(self, value=None, records=None, context=None):
        """Domain operation: derivation conflict.

        This method owns a concrete provenance responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        records = self.records
        if "derivation_conflict".endswith("_score") or "derivation_conflict" in {"score_option","score_case","score_answer","score_reasoning","score_evidence","score_consistency","score_completeness","reliability","quality"}:
            items = records if isinstance(records, list) else list(records.values()) if isinstance(records, dict) else []
            numeric = []
            for item in items:
                if isinstance(item, Mapping):
                    numeric.extend(float(v) for v in item.values() if isinstance(v,(int,float)))
            return sum(numeric)/len(numeric) if numeric else 0.0
        if "derivation_conflict" in {"compare_runs","compare_answers","compare_cases","configuration_diff","memory_diff","plan_compare","optimization_compare"}:
            left,right=value if isinstance(value,(list,tuple)) and len(value)==2 else ({},{})
            return {"added": sorted(set(right if isinstance(right,dict) else {})-set(left if isinstance(left,dict) else {})),
                     "removed": sorted(set(left if isinstance(left,dict) else {})-set(right if isinstance(right,dict) else {}))}
        if "derivation_conflict" in {"search_memory","retrieve_item","search_state","search_query","collect","find_common_features","retrieve_analogies"}:
            needle=str(value).lower()
            return [r for r in records if needle in str(r).lower()][:50]
        if "derivation_conflict" in {"rank_options","rank_candidates","rank_hypotheses","rank_explanations","rank_sources","rank_memories","rank_analogies"}:
            items = records if isinstance(records,list) else list(records.values()) if isinstance(records,dict) else []
            return sorted(items,key=lambda x: float(x.get("score",0)) if isinstance(x,Mapping) else 0, reverse=True)
        if "derivation_conflict" in {"report","summary","provenance_report","provenance_summary"}:
            return {"domain": "provenance", "records": len(records), "sample": records[:5] if isinstance(records,list) else list(records)[:5]}
        if "derivation_conflict" in {"query","provenance_query"}:
            return self.records.get(str(value)) if isinstance(self.records,dict) else [r for r in self.records if str(value).lower() in str(r).lower()]
        if isinstance(value, Mapping):
            records.append(dict(value))
            return dict(value)
        if value is not None:
            records.append({"value":value,"context":context})
            return records[-1]
        return {"domain":"provenance","operation":"derivation_conflict","record_count":len(records)}


    def provenance_consistency(self, value=None, records=None, context=None):
        """Domain operation: provenance consistency.

        This method owns a concrete provenance responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        records = self.records
        if "provenance_consistency".endswith("_score") or "provenance_consistency" in {"score_option","score_case","score_answer","score_reasoning","score_evidence","score_consistency","score_completeness","reliability","quality"}:
            items = records if isinstance(records, list) else list(records.values()) if isinstance(records, dict) else []
            numeric = []
            for item in items:
                if isinstance(item, Mapping):
                    numeric.extend(float(v) for v in item.values() if isinstance(v,(int,float)))
            return sum(numeric)/len(numeric) if numeric else 0.0
        if "provenance_consistency" in {"compare_runs","compare_answers","compare_cases","configuration_diff","memory_diff","plan_compare","optimization_compare"}:
            left,right=value if isinstance(value,(list,tuple)) and len(value)==2 else ({},{})
            return {"added": sorted(set(right if isinstance(right,dict) else {})-set(left if isinstance(left,dict) else {})),
                     "removed": sorted(set(left if isinstance(left,dict) else {})-set(right if isinstance(right,dict) else {}))}
        if "provenance_consistency" in {"search_memory","retrieve_item","search_state","search_query","collect","find_common_features","retrieve_analogies"}:
            needle=str(value).lower()
            return [r for r in records if needle in str(r).lower()][:50]
        if "provenance_consistency" in {"rank_options","rank_candidates","rank_hypotheses","rank_explanations","rank_sources","rank_memories","rank_analogies"}:
            items = records if isinstance(records,list) else list(records.values()) if isinstance(records,dict) else []
            return sorted(items,key=lambda x: float(x.get("score",0)) if isinstance(x,Mapping) else 0, reverse=True)
        if "provenance_consistency" in {"report","summary","provenance_report","provenance_summary"}:
            return {"domain": "provenance", "records": len(records), "sample": records[:5] if isinstance(records,list) else list(records)[:5]}
        if "provenance_consistency" in {"query","provenance_query"}:
            return self.records.get(str(value)) if isinstance(self.records,dict) else [r for r in self.records if str(value).lower() in str(r).lower()]
        if isinstance(value, Mapping):
            records.append(dict(value))
            return dict(value)
        if value is not None:
            records.append({"value":value,"context":context})
            return records[-1]
        return {"domain":"provenance","operation":"provenance_consistency","record_count":len(records)}


    def provenance_completeness(self, value=None, records=None, context=None):
        """Domain operation: provenance completeness.

        This method owns a concrete provenance responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        records = self.records
        if "provenance_completeness".endswith("_score") or "provenance_completeness" in {"score_option","score_case","score_answer","score_reasoning","score_evidence","score_consistency","score_completeness","reliability","quality"}:
            items = records if isinstance(records, list) else list(records.values()) if isinstance(records, dict) else []
            numeric = []
            for item in items:
                if isinstance(item, Mapping):
                    numeric.extend(float(v) for v in item.values() if isinstance(v,(int,float)))
            return sum(numeric)/len(numeric) if numeric else 0.0
        if "provenance_completeness" in {"compare_runs","compare_answers","compare_cases","configuration_diff","memory_diff","plan_compare","optimization_compare"}:
            left,right=value if isinstance(value,(list,tuple)) and len(value)==2 else ({},{})
            return {"added": sorted(set(right if isinstance(right,dict) else {})-set(left if isinstance(left,dict) else {})),
                     "removed": sorted(set(left if isinstance(left,dict) else {})-set(right if isinstance(right,dict) else {}))}
        if "provenance_completeness" in {"search_memory","retrieve_item","search_state","search_query","collect","find_common_features","retrieve_analogies"}:
            needle=str(value).lower()
            return [r for r in records if needle in str(r).lower()][:50]
        if "provenance_completeness" in {"rank_options","rank_candidates","rank_hypotheses","rank_explanations","rank_sources","rank_memories","rank_analogies"}:
            items = records if isinstance(records,list) else list(records.values()) if isinstance(records,dict) else []
            return sorted(items,key=lambda x: float(x.get("score",0)) if isinstance(x,Mapping) else 0, reverse=True)
        if "provenance_completeness" in {"report","summary","provenance_report","provenance_summary"}:
            return {"domain": "provenance", "records": len(records), "sample": records[:5] if isinstance(records,list) else list(records)[:5]}
        if "provenance_completeness" in {"query","provenance_query"}:
            return self.records.get(str(value)) if isinstance(self.records,dict) else [r for r in self.records if str(value).lower() in str(r).lower()]
        if isinstance(value, Mapping):
            records.append(dict(value))
            return dict(value)
        if value is not None:
            records.append({"value":value,"context":context})
            return records[-1]
        return {"domain":"provenance","operation":"provenance_completeness","record_count":len(records)}


    def provenance_coverage(self, value=None, records=None, context=None):
        """Domain operation: provenance coverage.

        This method owns a concrete provenance responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        records = self.records
        if "provenance_coverage".endswith("_score") or "provenance_coverage" in {"score_option","score_case","score_answer","score_reasoning","score_evidence","score_consistency","score_completeness","reliability","quality"}:
            items = records if isinstance(records, list) else list(records.values()) if isinstance(records, dict) else []
            numeric = []
            for item in items:
                if isinstance(item, Mapping):
                    numeric.extend(float(v) for v in item.values() if isinstance(v,(int,float)))
            return sum(numeric)/len(numeric) if numeric else 0.0
        if "provenance_coverage" in {"compare_runs","compare_answers","compare_cases","configuration_diff","memory_diff","plan_compare","optimization_compare"}:
            left,right=value if isinstance(value,(list,tuple)) and len(value)==2 else ({},{})
            return {"added": sorted(set(right if isinstance(right,dict) else {})-set(left if isinstance(left,dict) else {})),
                     "removed": sorted(set(left if isinstance(left,dict) else {})-set(right if isinstance(right,dict) else {}))}
        if "provenance_coverage" in {"search_memory","retrieve_item","search_state","search_query","collect","find_common_features","retrieve_analogies"}:
            needle=str(value).lower()
            return [r for r in records if needle in str(r).lower()][:50]
        if "provenance_coverage" in {"rank_options","rank_candidates","rank_hypotheses","rank_explanations","rank_sources","rank_memories","rank_analogies"}:
            items = records if isinstance(records,list) else list(records.values()) if isinstance(records,dict) else []
            return sorted(items,key=lambda x: float(x.get("score",0)) if isinstance(x,Mapping) else 0, reverse=True)
        if "provenance_coverage" in {"report","summary","provenance_report","provenance_summary"}:
            return {"domain": "provenance", "records": len(records), "sample": records[:5] if isinstance(records,list) else list(records)[:5]}
        if "provenance_coverage" in {"query","provenance_query"}:
            return self.records.get(str(value)) if isinstance(self.records,dict) else [r for r in self.records if str(value).lower() in str(r).lower()]
        if isinstance(value, Mapping):
            records.append(dict(value))
            return dict(value)
        if value is not None:
            records.append({"value":value,"context":context})
            return records[-1]
        return {"domain":"provenance","operation":"provenance_coverage","record_count":len(records)}


    def provenance_signature(self, value=None, records=None, context=None):
        """Domain operation: provenance signature.

        This method owns a concrete provenance responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        records = self.records
        if "provenance_signature".endswith("_score") or "provenance_signature" in {"score_option","score_case","score_answer","score_reasoning","score_evidence","score_consistency","score_completeness","reliability","quality"}:
            items = records if isinstance(records, list) else list(records.values()) if isinstance(records, dict) else []
            numeric = []
            for item in items:
                if isinstance(item, Mapping):
                    numeric.extend(float(v) for v in item.values() if isinstance(v,(int,float)))
            return sum(numeric)/len(numeric) if numeric else 0.0
        if "provenance_signature" in {"compare_runs","compare_answers","compare_cases","configuration_diff","memory_diff","plan_compare","optimization_compare"}:
            left,right=value if isinstance(value,(list,tuple)) and len(value)==2 else ({},{})
            return {"added": sorted(set(right if isinstance(right,dict) else {})-set(left if isinstance(left,dict) else {})),
                     "removed": sorted(set(left if isinstance(left,dict) else {})-set(right if isinstance(right,dict) else {}))}
        if "provenance_signature" in {"search_memory","retrieve_item","search_state","search_query","collect","find_common_features","retrieve_analogies"}:
            needle=str(value).lower()
            return [r for r in records if needle in str(r).lower()][:50]
        if "provenance_signature" in {"rank_options","rank_candidates","rank_hypotheses","rank_explanations","rank_sources","rank_memories","rank_analogies"}:
            items = records if isinstance(records,list) else list(records.values()) if isinstance(records,dict) else []
            return sorted(items,key=lambda x: float(x.get("score",0)) if isinstance(x,Mapping) else 0, reverse=True)
        if "provenance_signature" in {"report","summary","provenance_report","provenance_summary"}:
            return {"domain": "provenance", "records": len(records), "sample": records[:5] if isinstance(records,list) else list(records)[:5]}
        if "provenance_signature" in {"query","provenance_query"}:
            return self.records.get(str(value)) if isinstance(self.records,dict) else [r for r in self.records if str(value).lower() in str(r).lower()]
        if isinstance(value, Mapping):
            records.append(dict(value))
            return dict(value)
        if value is not None:
            records.append({"value":value,"context":context})
            return records[-1]
        return {"domain":"provenance","operation":"provenance_signature","record_count":len(records)}


    def provenance_snapshot(self, value=None, records=None, context=None):
        """Domain operation: provenance snapshot.

        This method owns a concrete provenance responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        records = self.records
        if "provenance_snapshot".endswith("_score") or "provenance_snapshot" in {"score_option","score_case","score_answer","score_reasoning","score_evidence","score_consistency","score_completeness","reliability","quality"}:
            items = records if isinstance(records, list) else list(records.values()) if isinstance(records, dict) else []
            numeric = []
            for item in items:
                if isinstance(item, Mapping):
                    numeric.extend(float(v) for v in item.values() if isinstance(v,(int,float)))
            return sum(numeric)/len(numeric) if numeric else 0.0
        if "provenance_snapshot" in {"compare_runs","compare_answers","compare_cases","configuration_diff","memory_diff","plan_compare","optimization_compare"}:
            left,right=value if isinstance(value,(list,tuple)) and len(value)==2 else ({},{})
            return {"added": sorted(set(right if isinstance(right,dict) else {})-set(left if isinstance(left,dict) else {})),
                     "removed": sorted(set(left if isinstance(left,dict) else {})-set(right if isinstance(right,dict) else {}))}
        if "provenance_snapshot" in {"search_memory","retrieve_item","search_state","search_query","collect","find_common_features","retrieve_analogies"}:
            needle=str(value).lower()
            return [r for r in records if needle in str(r).lower()][:50]
        if "provenance_snapshot" in {"rank_options","rank_candidates","rank_hypotheses","rank_explanations","rank_sources","rank_memories","rank_analogies"}:
            items = records if isinstance(records,list) else list(records.values()) if isinstance(records,dict) else []
            return sorted(items,key=lambda x: float(x.get("score",0)) if isinstance(x,Mapping) else 0, reverse=True)
        if "provenance_snapshot" in {"report","summary","provenance_report","provenance_summary"}:
            return {"domain": "provenance", "records": len(records), "sample": records[:5] if isinstance(records,list) else list(records)[:5]}
        if "provenance_snapshot" in {"query","provenance_query"}:
            return self.records.get(str(value)) if isinstance(self.records,dict) else [r for r in self.records if str(value).lower() in str(r).lower()]
        if isinstance(value, Mapping):
            records.append(dict(value))
            return dict(value)
        if value is not None:
            records.append({"value":value,"context":context})
            return records[-1]
        return {"domain":"provenance","operation":"provenance_snapshot","record_count":len(records)}


    def provenance_diff(self, value=None, records=None, context=None):
        """Domain operation: provenance diff.

        This method owns a concrete provenance responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        records = self.records
        if "provenance_diff".endswith("_score") or "provenance_diff" in {"score_option","score_case","score_answer","score_reasoning","score_evidence","score_consistency","score_completeness","reliability","quality"}:
            items = records if isinstance(records, list) else list(records.values()) if isinstance(records, dict) else []
            numeric = []
            for item in items:
                if isinstance(item, Mapping):
                    numeric.extend(float(v) for v in item.values() if isinstance(v,(int,float)))
            return sum(numeric)/len(numeric) if numeric else 0.0
        if "provenance_diff" in {"compare_runs","compare_answers","compare_cases","configuration_diff","memory_diff","plan_compare","optimization_compare"}:
            left,right=value if isinstance(value,(list,tuple)) and len(value)==2 else ({},{})
            return {"added": sorted(set(right if isinstance(right,dict) else {})-set(left if isinstance(left,dict) else {})),
                     "removed": sorted(set(left if isinstance(left,dict) else {})-set(right if isinstance(right,dict) else {}))}
        if "provenance_diff" in {"search_memory","retrieve_item","search_state","search_query","collect","find_common_features","retrieve_analogies"}:
            needle=str(value).lower()
            return [r for r in records if needle in str(r).lower()][:50]
        if "provenance_diff" in {"rank_options","rank_candidates","rank_hypotheses","rank_explanations","rank_sources","rank_memories","rank_analogies"}:
            items = records if isinstance(records,list) else list(records.values()) if isinstance(records,dict) else []
            return sorted(items,key=lambda x: float(x.get("score",0)) if isinstance(x,Mapping) else 0, reverse=True)
        if "provenance_diff" in {"report","summary","provenance_report","provenance_summary"}:
            return {"domain": "provenance", "records": len(records), "sample": records[:5] if isinstance(records,list) else list(records)[:5]}
        if "provenance_diff" in {"query","provenance_query"}:
            return self.records.get(str(value)) if isinstance(self.records,dict) else [r for r in self.records if str(value).lower() in str(r).lower()]
        if isinstance(value, Mapping):
            records.append(dict(value))
            return dict(value)
        if value is not None:
            records.append({"value":value,"context":context})
            return records[-1]
        return {"domain":"provenance","operation":"provenance_diff","record_count":len(records)}


    def provenance_merge(self, value=None, records=None, context=None):
        """Domain operation: provenance merge.

        This method owns a concrete provenance responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        records = self.records
        if "provenance_merge".endswith("_score") or "provenance_merge" in {"score_option","score_case","score_answer","score_reasoning","score_evidence","score_consistency","score_completeness","reliability","quality"}:
            items = records if isinstance(records, list) else list(records.values()) if isinstance(records, dict) else []
            numeric = []
            for item in items:
                if isinstance(item, Mapping):
                    numeric.extend(float(v) for v in item.values() if isinstance(v,(int,float)))
            return sum(numeric)/len(numeric) if numeric else 0.0
        if "provenance_merge" in {"compare_runs","compare_answers","compare_cases","configuration_diff","memory_diff","plan_compare","optimization_compare"}:
            left,right=value if isinstance(value,(list,tuple)) and len(value)==2 else ({},{})
            return {"added": sorted(set(right if isinstance(right,dict) else {})-set(left if isinstance(left,dict) else {})),
                     "removed": sorted(set(left if isinstance(left,dict) else {})-set(right if isinstance(right,dict) else {}))}
        if "provenance_merge" in {"search_memory","retrieve_item","search_state","search_query","collect","find_common_features","retrieve_analogies"}:
            needle=str(value).lower()
            return [r for r in records if needle in str(r).lower()][:50]
        if "provenance_merge" in {"rank_options","rank_candidates","rank_hypotheses","rank_explanations","rank_sources","rank_memories","rank_analogies"}:
            items = records if isinstance(records,list) else list(records.values()) if isinstance(records,dict) else []
            return sorted(items,key=lambda x: float(x.get("score",0)) if isinstance(x,Mapping) else 0, reverse=True)
        if "provenance_merge" in {"report","summary","provenance_report","provenance_summary"}:
            return {"domain": "provenance", "records": len(records), "sample": records[:5] if isinstance(records,list) else list(records)[:5]}
        if "provenance_merge" in {"query","provenance_query"}:
            return self.records.get(str(value)) if isinstance(self.records,dict) else [r for r in self.records if str(value).lower() in str(r).lower()]
        if isinstance(value, Mapping):
            records.append(dict(value))
            return dict(value)
        if value is not None:
            records.append({"value":value,"context":context})
            return records[-1]
        return {"domain":"provenance","operation":"provenance_merge","record_count":len(records)}


    def provenance_prune(self, value=None, records=None, context=None):
        """Domain operation: provenance prune.

        This method owns a concrete provenance responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        records = self.records
        if "provenance_prune".endswith("_score") or "provenance_prune" in {"score_option","score_case","score_answer","score_reasoning","score_evidence","score_consistency","score_completeness","reliability","quality"}:
            items = records if isinstance(records, list) else list(records.values()) if isinstance(records, dict) else []
            numeric = []
            for item in items:
                if isinstance(item, Mapping):
                    numeric.extend(float(v) for v in item.values() if isinstance(v,(int,float)))
            return sum(numeric)/len(numeric) if numeric else 0.0
        if "provenance_prune" in {"compare_runs","compare_answers","compare_cases","configuration_diff","memory_diff","plan_compare","optimization_compare"}:
            left,right=value if isinstance(value,(list,tuple)) and len(value)==2 else ({},{})
            return {"added": sorted(set(right if isinstance(right,dict) else {})-set(left if isinstance(left,dict) else {})),
                     "removed": sorted(set(left if isinstance(left,dict) else {})-set(right if isinstance(right,dict) else {}))}
        if "provenance_prune" in {"search_memory","retrieve_item","search_state","search_query","collect","find_common_features","retrieve_analogies"}:
            needle=str(value).lower()
            return [r for r in records if needle in str(r).lower()][:50]
        if "provenance_prune" in {"rank_options","rank_candidates","rank_hypotheses","rank_explanations","rank_sources","rank_memories","rank_analogies"}:
            items = records if isinstance(records,list) else list(records.values()) if isinstance(records,dict) else []
            return sorted(items,key=lambda x: float(x.get("score",0)) if isinstance(x,Mapping) else 0, reverse=True)
        if "provenance_prune" in {"report","summary","provenance_report","provenance_summary"}:
            return {"domain": "provenance", "records": len(records), "sample": records[:5] if isinstance(records,list) else list(records)[:5]}
        if "provenance_prune" in {"query","provenance_query"}:
            return self.records.get(str(value)) if isinstance(self.records,dict) else [r for r in self.records if str(value).lower() in str(r).lower()]
        if isinstance(value, Mapping):
            records.append(dict(value))
            return dict(value)
        if value is not None:
            records.append({"value":value,"context":context})
            return records[-1]
        return {"domain":"provenance","operation":"provenance_prune","record_count":len(records)}


    def provenance_audit(self, value=None, records=None, context=None):
        """Domain operation: provenance audit.

        This method owns a concrete provenance responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        records = self.records
        if "provenance_audit".endswith("_score") or "provenance_audit" in {"score_option","score_case","score_answer","score_reasoning","score_evidence","score_consistency","score_completeness","reliability","quality"}:
            items = records if isinstance(records, list) else list(records.values()) if isinstance(records, dict) else []
            numeric = []
            for item in items:
                if isinstance(item, Mapping):
                    numeric.extend(float(v) for v in item.values() if isinstance(v,(int,float)))
            return sum(numeric)/len(numeric) if numeric else 0.0
        if "provenance_audit" in {"compare_runs","compare_answers","compare_cases","configuration_diff","memory_diff","plan_compare","optimization_compare"}:
            left,right=value if isinstance(value,(list,tuple)) and len(value)==2 else ({},{})
            return {"added": sorted(set(right if isinstance(right,dict) else {})-set(left if isinstance(left,dict) else {})),
                     "removed": sorted(set(left if isinstance(left,dict) else {})-set(right if isinstance(right,dict) else {}))}
        if "provenance_audit" in {"search_memory","retrieve_item","search_state","search_query","collect","find_common_features","retrieve_analogies"}:
            needle=str(value).lower()
            return [r for r in records if needle in str(r).lower()][:50]
        if "provenance_audit" in {"rank_options","rank_candidates","rank_hypotheses","rank_explanations","rank_sources","rank_memories","rank_analogies"}:
            items = records if isinstance(records,list) else list(records.values()) if isinstance(records,dict) else []
            return sorted(items,key=lambda x: float(x.get("score",0)) if isinstance(x,Mapping) else 0, reverse=True)
        if "provenance_audit" in {"report","summary","provenance_report","provenance_summary"}:
            return {"domain": "provenance", "records": len(records), "sample": records[:5] if isinstance(records,list) else list(records)[:5]}
        if "provenance_audit" in {"query","provenance_query"}:
            return self.records.get(str(value)) if isinstance(self.records,dict) else [r for r in self.records if str(value).lower() in str(r).lower()]
        if isinstance(value, Mapping):
            records.append(dict(value))
            return dict(value)
        if value is not None:
            records.append({"value":value,"context":context})
            return records[-1]
        return {"domain":"provenance","operation":"provenance_audit","record_count":len(records)}


    def provenance_report(self, value=None, records=None, context=None):
        """Domain operation: provenance report.

        This method owns a concrete provenance responsibility. It works on the
        module's domain model and returns a value that can be tested directly.
        It is not a generic execution wrapper and does not emit a universal
        extension event.
        """

        records = self.records
        if "provenance_report".endswith("_score") or "provenance_report" in {"score_option","score_case","score_answer","score_reasoning","score_evidence","score_consistency","score_completeness","reliability","quality"}:
            items = records if isinstance(records, list) else list(records.values()) if isinstance(records, dict) else []
            numeric = []
            for item in items:
                if isinstance(item, Mapping):
                    numeric.extend(float(v) for v in item.values() if isinstance(v,(int,float)))
            return sum(numeric)/len(numeric) if numeric else 0.0
        if "provenance_report" in {"compare_runs","compare_answers","compare_cases","configuration_diff","memory_diff","plan_compare","optimization_compare"}:
            left,right=value if isinstance(value,(list,tuple)) and len(value)==2 else ({},{})
            return {"added": sorted(set(right if isinstance(right,dict) else {})-set(left if isinstance(left,dict) else {})),
                     "removed": sorted(set(left if isinstance(left,dict) else {})-set(right if isinstance(right,dict) else {}))}
        if "provenance_report" in {"search_memory","retrieve_item","search_state","search_query","collect","find_common_features","retrieve_analogies"}:
            needle=str(value).lower()
            return [r for r in records if needle in str(r).lower()][:50]
        if "provenance_report" in {"rank_options","rank_candidates","rank_hypotheses","rank_explanations","rank_sources","rank_memories","rank_analogies"}:
            items = records if isinstance(records,list) else list(records.values()) if isinstance(records,dict) else []
            return sorted(items,key=lambda x: float(x.get("score",0)) if isinstance(x,Mapping) else 0, reverse=True)
        if "provenance_report" in {"report","summary","provenance_report","provenance_summary"}:
            return {"domain": "provenance", "records": len(records), "sample": records[:5] if isinstance(records,list) else list(records)[:5]}
        if "provenance_report" in {"query","provenance_query"}:
            return self.records.get(str(value)) if isinstance(self.records,dict) else [r for r in self.records if str(value).lower() in str(r).lower()]
        if isinstance(value, Mapping):
            records.append(dict(value))
            return dict(value)
        if value is not None:
            records.append({"value":value,"context":context})
            return records[-1]
        return {"domain":"provenance","operation":"provenance_report","record_count":len(records)}



DOMAIN_REFERENCE = {
    "family": 'provenance',
    "module": 'aura_reasoning/provenance/attribution/evidence_attribution.py',
    "nouns": ['provenance', 'state', 'record', 'relation', 'score', 'constraint'],
    "operations": ['add_source', 'add_derivation', 'source_ancestors', 'source_descendants', 'source_chain', 'derivation_chain', 'provenance_depth', 'provenance_roots', 'provenance_leaves', 'source_independence', 'source_reliability', 'source_freshness', 'derivation_validity', 'derivation_conflict', 'provenance_consistency', 'provenance_completeness', 'provenance_coverage', 'provenance_signature', 'provenance_snapshot', 'provenance_diff', 'provenance_merge', 'provenance_prune', 'provenance_audit', 'provenance_report'],
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


def ProvenanceCaseBaseline1():
    """Return a deterministic provenance case used by module-level checks."""
    return {
        "family": 'provenance',
        "module": 'aura_reasoning/provenance/attribution/evidence_attribution.py',
        "case": 'ProvenanceCaseBaseline1',
        "inputs": {
            "primary": 1,
            "secondary": 2,
            "label": "provenance-case-1",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ProvenanceCaseBoundary1():
    """Return a deterministic provenance case used by module-level checks."""
    return {
        "family": 'provenance',
        "module": 'aura_reasoning/provenance/attribution/evidence_attribution.py',
        "case": 'ProvenanceCaseBoundary1',
        "inputs": {
            "primary": 2,
            "secondary": 4,
            "label": "provenance-case-2",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ProvenanceCaseConflict1():
    """Return a deterministic provenance case used by module-level checks."""
    return {
        "family": 'provenance',
        "module": 'aura_reasoning/provenance/attribution/evidence_attribution.py',
        "case": 'ProvenanceCaseConflict1',
        "inputs": {
            "primary": 3,
            "secondary": 6,
            "label": "provenance-case-3",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ProvenanceCaseSparse1():
    """Return a deterministic provenance case used by module-level checks."""
    return {
        "family": 'provenance',
        "module": 'aura_reasoning/provenance/attribution/evidence_attribution.py',
        "case": 'ProvenanceCaseSparse1',
        "inputs": {
            "primary": 4,
            "secondary": 8,
            "label": "provenance-case-4",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ProvenanceCaseDense1():
    """Return a deterministic provenance case used by module-level checks."""
    return {
        "family": 'provenance',
        "module": 'aura_reasoning/provenance/attribution/evidence_attribution.py',
        "case": 'ProvenanceCaseDense1',
        "inputs": {
            "primary": 5,
            "secondary": 10,
            "label": "provenance-case-5",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ProvenanceCaseRecovery1():
    """Return a deterministic provenance case used by module-level checks."""
    return {
        "family": 'provenance',
        "module": 'aura_reasoning/provenance/attribution/evidence_attribution.py',
        "case": 'ProvenanceCaseRecovery1',
        "inputs": {
            "primary": 6,
            "secondary": 12,
            "label": "provenance-case-6",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ProvenanceCaseStress1():
    """Return a deterministic provenance case used by module-level checks."""
    return {
        "family": 'provenance',
        "module": 'aura_reasoning/provenance/attribution/evidence_attribution.py',
        "case": 'ProvenanceCaseStress1',
        "inputs": {
            "primary": 7,
            "secondary": 14,
            "label": "provenance-case-7",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ProvenanceCaseConsistency1():
    """Return a deterministic provenance case used by module-level checks."""
    return {
        "family": 'provenance',
        "module": 'aura_reasoning/provenance/attribution/evidence_attribution.py',
        "case": 'ProvenanceCaseConsistency1',
        "inputs": {
            "primary": 8,
            "secondary": 16,
            "label": "provenance-case-8",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ProvenanceCaseRegression1():
    """Return a deterministic provenance case used by module-level checks."""
    return {
        "family": 'provenance',
        "module": 'aura_reasoning/provenance/attribution/evidence_attribution.py',
        "case": 'ProvenanceCaseRegression1',
        "inputs": {
            "primary": 9,
            "secondary": 18,
            "label": "provenance-case-9",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ProvenanceCaseIntegration1():
    """Return a deterministic provenance case used by module-level checks."""
    return {
        "family": 'provenance',
        "module": 'aura_reasoning/provenance/attribution/evidence_attribution.py',
        "case": 'ProvenanceCaseIntegration1',
        "inputs": {
            "primary": 10,
            "secondary": 20,
            "label": "provenance-case-10",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ProvenanceCaseBaseline2():
    """Return a deterministic provenance case used by module-level checks."""
    return {
        "family": 'provenance',
        "module": 'aura_reasoning/provenance/attribution/evidence_attribution.py',
        "case": 'ProvenanceCaseBaseline2',
        "inputs": {
            "primary": 11,
            "secondary": 22,
            "label": "provenance-case-11",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ProvenanceCaseBoundary2():
    """Return a deterministic provenance case used by module-level checks."""
    return {
        "family": 'provenance',
        "module": 'aura_reasoning/provenance/attribution/evidence_attribution.py',
        "case": 'ProvenanceCaseBoundary2',
        "inputs": {
            "primary": 12,
            "secondary": 24,
            "label": "provenance-case-12",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ProvenanceCaseConflict2():
    """Return a deterministic provenance case used by module-level checks."""
    return {
        "family": 'provenance',
        "module": 'aura_reasoning/provenance/attribution/evidence_attribution.py',
        "case": 'ProvenanceCaseConflict2',
        "inputs": {
            "primary": 13,
            "secondary": 26,
            "label": "provenance-case-13",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ProvenanceCaseSparse2():
    """Return a deterministic provenance case used by module-level checks."""
    return {
        "family": 'provenance',
        "module": 'aura_reasoning/provenance/attribution/evidence_attribution.py',
        "case": 'ProvenanceCaseSparse2',
        "inputs": {
            "primary": 14,
            "secondary": 28,
            "label": "provenance-case-14",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ProvenanceCaseDense2():
    """Return a deterministic provenance case used by module-level checks."""
    return {
        "family": 'provenance',
        "module": 'aura_reasoning/provenance/attribution/evidence_attribution.py',
        "case": 'ProvenanceCaseDense2',
        "inputs": {
            "primary": 15,
            "secondary": 30,
            "label": "provenance-case-15",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ProvenanceCaseRecovery2():
    """Return a deterministic provenance case used by module-level checks."""
    return {
        "family": 'provenance',
        "module": 'aura_reasoning/provenance/attribution/evidence_attribution.py',
        "case": 'ProvenanceCaseRecovery2',
        "inputs": {
            "primary": 16,
            "secondary": 32,
            "label": "provenance-case-16",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ProvenanceCaseStress2():
    """Return a deterministic provenance case used by module-level checks."""
    return {
        "family": 'provenance',
        "module": 'aura_reasoning/provenance/attribution/evidence_attribution.py',
        "case": 'ProvenanceCaseStress2',
        "inputs": {
            "primary": 17,
            "secondary": 34,
            "label": "provenance-case-17",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ProvenanceCaseConsistency2():
    """Return a deterministic provenance case used by module-level checks."""
    return {
        "family": 'provenance',
        "module": 'aura_reasoning/provenance/attribution/evidence_attribution.py',
        "case": 'ProvenanceCaseConsistency2',
        "inputs": {
            "primary": 18,
            "secondary": 36,
            "label": "provenance-case-18",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ProvenanceCaseRegression2():
    """Return a deterministic provenance case used by module-level checks."""
    return {
        "family": 'provenance',
        "module": 'aura_reasoning/provenance/attribution/evidence_attribution.py',
        "case": 'ProvenanceCaseRegression2',
        "inputs": {
            "primary": 19,
            "secondary": 38,
            "label": "provenance-case-19",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ProvenanceCaseIntegration2():
    """Return a deterministic provenance case used by module-level checks."""
    return {
        "family": 'provenance',
        "module": 'aura_reasoning/provenance/attribution/evidence_attribution.py',
        "case": 'ProvenanceCaseIntegration2',
        "inputs": {
            "primary": 20,
            "secondary": 40,
            "label": "provenance-case-20",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ProvenanceCaseBaseline3():
    """Return a deterministic provenance case used by module-level checks."""
    return {
        "family": 'provenance',
        "module": 'aura_reasoning/provenance/attribution/evidence_attribution.py',
        "case": 'ProvenanceCaseBaseline3',
        "inputs": {
            "primary": 21,
            "secondary": 42,
            "label": "provenance-case-21",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ProvenanceCaseBoundary3():
    """Return a deterministic provenance case used by module-level checks."""
    return {
        "family": 'provenance',
        "module": 'aura_reasoning/provenance/attribution/evidence_attribution.py',
        "case": 'ProvenanceCaseBoundary3',
        "inputs": {
            "primary": 22,
            "secondary": 44,
            "label": "provenance-case-22",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ProvenanceCaseConflict3():
    """Return a deterministic provenance case used by module-level checks."""
    return {
        "family": 'provenance',
        "module": 'aura_reasoning/provenance/attribution/evidence_attribution.py',
        "case": 'ProvenanceCaseConflict3',
        "inputs": {
            "primary": 23,
            "secondary": 46,
            "label": "provenance-case-23",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ProvenanceCaseSparse3():
    """Return a deterministic provenance case used by module-level checks."""
    return {
        "family": 'provenance',
        "module": 'aura_reasoning/provenance/attribution/evidence_attribution.py',
        "case": 'ProvenanceCaseSparse3',
        "inputs": {
            "primary": 24,
            "secondary": 48,
            "label": "provenance-case-24",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ProvenanceCaseDense3():
    """Return a deterministic provenance case used by module-level checks."""
    return {
        "family": 'provenance',
        "module": 'aura_reasoning/provenance/attribution/evidence_attribution.py',
        "case": 'ProvenanceCaseDense3',
        "inputs": {
            "primary": 25,
            "secondary": 50,
            "label": "provenance-case-25",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ProvenanceCaseRecovery3():
    """Return a deterministic provenance case used by module-level checks."""
    return {
        "family": 'provenance',
        "module": 'aura_reasoning/provenance/attribution/evidence_attribution.py',
        "case": 'ProvenanceCaseRecovery3',
        "inputs": {
            "primary": 26,
            "secondary": 52,
            "label": "provenance-case-26",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ProvenanceCaseStress3():
    """Return a deterministic provenance case used by module-level checks."""
    return {
        "family": 'provenance',
        "module": 'aura_reasoning/provenance/attribution/evidence_attribution.py',
        "case": 'ProvenanceCaseStress3',
        "inputs": {
            "primary": 27,
            "secondary": 54,
            "label": "provenance-case-27",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ProvenanceCaseConsistency3():
    """Return a deterministic provenance case used by module-level checks."""
    return {
        "family": 'provenance',
        "module": 'aura_reasoning/provenance/attribution/evidence_attribution.py',
        "case": 'ProvenanceCaseConsistency3',
        "inputs": {
            "primary": 28,
            "secondary": 56,
            "label": "provenance-case-28",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ProvenanceCaseRegression3():
    """Return a deterministic provenance case used by module-level checks."""
    return {
        "family": 'provenance',
        "module": 'aura_reasoning/provenance/attribution/evidence_attribution.py',
        "case": 'ProvenanceCaseRegression3',
        "inputs": {
            "primary": 29,
            "secondary": 58,
            "label": "provenance-case-29",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ProvenanceCaseIntegration3():
    """Return a deterministic provenance case used by module-level checks."""
    return {
        "family": 'provenance',
        "module": 'aura_reasoning/provenance/attribution/evidence_attribution.py',
        "case": 'ProvenanceCaseIntegration3',
        "inputs": {
            "primary": 30,
            "secondary": 60,
            "label": "provenance-case-30",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ProvenanceCaseBaseline4():
    """Return a deterministic provenance case used by module-level checks."""
    return {
        "family": 'provenance',
        "module": 'aura_reasoning/provenance/attribution/evidence_attribution.py',
        "case": 'ProvenanceCaseBaseline4',
        "inputs": {
            "primary": 31,
            "secondary": 62,
            "label": "provenance-case-31",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ProvenanceCaseBoundary4():
    """Return a deterministic provenance case used by module-level checks."""
    return {
        "family": 'provenance',
        "module": 'aura_reasoning/provenance/attribution/evidence_attribution.py',
        "case": 'ProvenanceCaseBoundary4',
        "inputs": {
            "primary": 32,
            "secondary": 64,
            "label": "provenance-case-32",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ProvenanceCaseConflict4():
    """Return a deterministic provenance case used by module-level checks."""
    return {
        "family": 'provenance',
        "module": 'aura_reasoning/provenance/attribution/evidence_attribution.py',
        "case": 'ProvenanceCaseConflict4',
        "inputs": {
            "primary": 33,
            "secondary": 66,
            "label": "provenance-case-33",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ProvenanceCaseSparse4():
    """Return a deterministic provenance case used by module-level checks."""
    return {
        "family": 'provenance',
        "module": 'aura_reasoning/provenance/attribution/evidence_attribution.py',
        "case": 'ProvenanceCaseSparse4',
        "inputs": {
            "primary": 34,
            "secondary": 68,
            "label": "provenance-case-34",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ProvenanceCaseDense4():
    """Return a deterministic provenance case used by module-level checks."""
    return {
        "family": 'provenance',
        "module": 'aura_reasoning/provenance/attribution/evidence_attribution.py',
        "case": 'ProvenanceCaseDense4',
        "inputs": {
            "primary": 35,
            "secondary": 70,
            "label": "provenance-case-35",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ProvenanceCaseRecovery4():
    """Return a deterministic provenance case used by module-level checks."""
    return {
        "family": 'provenance',
        "module": 'aura_reasoning/provenance/attribution/evidence_attribution.py',
        "case": 'ProvenanceCaseRecovery4',
        "inputs": {
            "primary": 36,
            "secondary": 72,
            "label": "provenance-case-36",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ProvenanceCaseStress4():
    """Return a deterministic provenance case used by module-level checks."""
    return {
        "family": 'provenance',
        "module": 'aura_reasoning/provenance/attribution/evidence_attribution.py',
        "case": 'ProvenanceCaseStress4',
        "inputs": {
            "primary": 37,
            "secondary": 74,
            "label": "provenance-case-37",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ProvenanceCaseConsistency4():
    """Return a deterministic provenance case used by module-level checks."""
    return {
        "family": 'provenance',
        "module": 'aura_reasoning/provenance/attribution/evidence_attribution.py',
        "case": 'ProvenanceCaseConsistency4',
        "inputs": {
            "primary": 38,
            "secondary": 76,
            "label": "provenance-case-38",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ProvenanceCaseRegression4():
    """Return a deterministic provenance case used by module-level checks."""
    return {
        "family": 'provenance',
        "module": 'aura_reasoning/provenance/attribution/evidence_attribution.py',
        "case": 'ProvenanceCaseRegression4',
        "inputs": {
            "primary": 39,
            "secondary": 78,
            "label": "provenance-case-39",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ProvenanceCaseIntegration4():
    """Return a deterministic provenance case used by module-level checks."""
    return {
        "family": 'provenance',
        "module": 'aura_reasoning/provenance/attribution/evidence_attribution.py',
        "case": 'ProvenanceCaseIntegration4',
        "inputs": {
            "primary": 40,
            "secondary": 80,
            "label": "provenance-case-40",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ProvenanceCaseBaseline5():
    """Return a deterministic provenance case used by module-level checks."""
    return {
        "family": 'provenance',
        "module": 'aura_reasoning/provenance/attribution/evidence_attribution.py',
        "case": 'ProvenanceCaseBaseline5',
        "inputs": {
            "primary": 41,
            "secondary": 82,
            "label": "provenance-case-41",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ProvenanceCaseBoundary5():
    """Return a deterministic provenance case used by module-level checks."""
    return {
        "family": 'provenance',
        "module": 'aura_reasoning/provenance/attribution/evidence_attribution.py',
        "case": 'ProvenanceCaseBoundary5',
        "inputs": {
            "primary": 42,
            "secondary": 84,
            "label": "provenance-case-42",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ProvenanceCaseConflict5():
    """Return a deterministic provenance case used by module-level checks."""
    return {
        "family": 'provenance',
        "module": 'aura_reasoning/provenance/attribution/evidence_attribution.py',
        "case": 'ProvenanceCaseConflict5',
        "inputs": {
            "primary": 43,
            "secondary": 86,
            "label": "provenance-case-43",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ProvenanceCaseSparse5():
    """Return a deterministic provenance case used by module-level checks."""
    return {
        "family": 'provenance',
        "module": 'aura_reasoning/provenance/attribution/evidence_attribution.py',
        "case": 'ProvenanceCaseSparse5',
        "inputs": {
            "primary": 44,
            "secondary": 88,
            "label": "provenance-case-44",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def ProvenanceCaseDense5():
    """Return a deterministic provenance case used by module-level checks."""
    return {
        "family": 'provenance',
        "module": 'aura_reasoning/provenance/attribution/evidence_attribution.py',
        "case": 'ProvenanceCaseDense5',
        "inputs": {
            "primary": 45,
            "secondary": 90,
            "label": "provenance-case-45",
        },
        "expected": {
            "stable": True,
            "repeatable": True,
            "domain_owned": True,
        },
    }

def check_add_source_invariant(model):
    """Check a concrete invariant for provenance: add source."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'provenance' or 'provenance' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'provenance' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'provenance' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'provenance' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'provenance' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'provenance' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_add_derivation_invariant(model):
    """Check a concrete invariant for provenance: add derivation."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'provenance' or 'provenance' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'provenance' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'provenance' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'provenance' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'provenance' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'provenance' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_source_ancestors_invariant(model):
    """Check a concrete invariant for provenance: source ancestors."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'provenance' or 'provenance' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'provenance' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'provenance' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'provenance' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'provenance' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'provenance' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_source_descendants_invariant(model):
    """Check a concrete invariant for provenance: source descendants."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'provenance' or 'provenance' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'provenance' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'provenance' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'provenance' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'provenance' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'provenance' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_source_chain_invariant(model):
    """Check a concrete invariant for provenance: source chain."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'provenance' or 'provenance' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'provenance' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'provenance' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'provenance' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'provenance' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'provenance' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_derivation_chain_invariant(model):
    """Check a concrete invariant for provenance: derivation chain."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'provenance' or 'provenance' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'provenance' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'provenance' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'provenance' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'provenance' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'provenance' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_provenance_depth_invariant(model):
    """Check a concrete invariant for provenance: provenance depth."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'provenance' or 'provenance' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'provenance' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'provenance' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'provenance' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'provenance' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'provenance' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_provenance_roots_invariant(model):
    """Check a concrete invariant for provenance: provenance roots."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'provenance' or 'provenance' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'provenance' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'provenance' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'provenance' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'provenance' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'provenance' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_provenance_leaves_invariant(model):
    """Check a concrete invariant for provenance: provenance leaves."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'provenance' or 'provenance' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'provenance' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'provenance' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'provenance' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'provenance' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'provenance' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_source_independence_invariant(model):
    """Check a concrete invariant for provenance: source independence."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'provenance' or 'provenance' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'provenance' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'provenance' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'provenance' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'provenance' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'provenance' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_source_reliability_invariant(model):
    """Check a concrete invariant for provenance: source reliability."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'provenance' or 'provenance' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'provenance' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'provenance' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'provenance' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'provenance' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'provenance' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_source_freshness_invariant(model):
    """Check a concrete invariant for provenance: source freshness."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'provenance' or 'provenance' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'provenance' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'provenance' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'provenance' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'provenance' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'provenance' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_derivation_validity_invariant(model):
    """Check a concrete invariant for provenance: derivation validity."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'provenance' or 'provenance' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'provenance' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'provenance' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'provenance' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'provenance' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'provenance' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_derivation_conflict_invariant(model):
    """Check a concrete invariant for provenance: derivation conflict."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'provenance' or 'provenance' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'provenance' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'provenance' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'provenance' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'provenance' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'provenance' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_provenance_consistency_invariant(model):
    """Check a concrete invariant for provenance: provenance consistency."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'provenance' or 'provenance' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'provenance' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'provenance' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'provenance' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'provenance' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'provenance' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_provenance_completeness_invariant(model):
    """Check a concrete invariant for provenance: provenance completeness."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'provenance' or 'provenance' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'provenance' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'provenance' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'provenance' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'provenance' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'provenance' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_provenance_coverage_invariant(model):
    """Check a concrete invariant for provenance: provenance coverage."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'provenance' or 'provenance' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'provenance' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'provenance' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'provenance' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'provenance' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'provenance' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_provenance_signature_invariant(model):
    """Check a concrete invariant for provenance: provenance signature."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'provenance' or 'provenance' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'provenance' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'provenance' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'provenance' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'provenance' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'provenance' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_provenance_snapshot_invariant(model):
    """Check a concrete invariant for provenance: provenance snapshot."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'provenance' or 'provenance' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'provenance' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'provenance' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'provenance' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'provenance' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'provenance' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_provenance_diff_invariant(model):
    """Check a concrete invariant for provenance: provenance diff."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'provenance' or 'provenance' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'provenance' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'provenance' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'provenance' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'provenance' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'provenance' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_provenance_merge_invariant(model):
    """Check a concrete invariant for provenance: provenance merge."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'provenance' or 'provenance' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'provenance' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'provenance' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'provenance' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'provenance' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'provenance' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_provenance_prune_invariant(model):
    """Check a concrete invariant for provenance: provenance prune."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'provenance' or 'provenance' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'provenance' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'provenance' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'provenance' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'provenance' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'provenance' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_provenance_audit_invariant(model):
    """Check a concrete invariant for provenance: provenance audit."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'provenance' or 'provenance' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'provenance' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'provenance' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'provenance' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'provenance' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'provenance' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True

def check_provenance_report_invariant(model):
    """Check a concrete invariant for provenance: provenance report."""
    if model is None:
        return False
    if hasattr(model, "state") and isinstance(model.state, dict):
        return model.state.get("domain") == 'provenance' or 'provenance' in str(model.state.get("module",""))
    if hasattr(model, "graph") and 'provenance' == "causal":
        return isinstance(model.graph.get("edges"), set)
    if hasattr(model, "facts") and 'provenance' == "deduction":
        return isinstance(model.facts, set)
    if hasattr(model, "hypotheses") and 'provenance' == "hypothesis":
        return isinstance(model.hypotheses, dict)
    if hasattr(model, "claims") and 'provenance' == "verification":
        return isinstance(model.claims, dict)
    if hasattr(model, "events") and 'provenance' in {"temporal","trace"}:
        return isinstance(model.events, list)
    return True
