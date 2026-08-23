from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from semantic_memory.engine import Engine as SemanticEngine
from episodic_memory.engine import Engine as EpisodicEngine
from procedural_memory.engine import Engine as ProceduralEngine
from associative_memory.engine import Engine as AssociativeEngine
from attention_memory.engine import Engine as AttentionEngine
from context_memory.engine import Engine as ContextEngine
from identity_memory.engine import Engine as IdentityEngine
from conversation_memory.engine import Engine as ConversationEngine
from task_memory.engine import Engine as TaskEngine
from knowledge_memory.engine import Engine as KnowledgeEngine
from memory_graph.graph_engine import GraphEngine
from reasoning.reasoning_engine import ReasoningEngine


class ExtendedMemoryEnginesTestCase(unittest.TestCase):
    def test_semantic_engine_returns_related_facts(self) -> None:
        engine = SemanticEngine()
        result = engine.process({"id": "s1", "content": "alpha", "concepts": ["alpha", "beta"], "strength": 0.8, "query": "alpha"})
        self.assertTrue(result["related_facts"])

    def test_episodic_engine_replays_recent_events(self) -> None:
        engine = EpisodicEngine()
        result = engine.process({"id": "e1", "content": "event", "importance": 0.9})
        self.assertEqual(result["replay"][0]["id"], "e1")

    def test_procedural_engine_ranks_procedures(self) -> None:
        engine = ProceduralEngine()
        engine.process({"id": "p1", "name": "login"})
        engine.reinforce("p1", succeeded=True)
        ranked = engine._rank_procedures()
        self.assertEqual(ranked[0]["id"], "p1")

    def test_associative_engine_spreads_activation(self) -> None:
        engine = AssociativeEngine()
        result = engine.process({"source": "a", "target": "b", "strength": 0.7})
        self.assertEqual(result["activations"][0]["target"], "b")

    def test_attention_engine_ranks_items(self) -> None:
        engine = AttentionEngine()
        result = engine.process({"items": [{"id": "1", "importance": 0.2}, {"id": "2", "importance": 0.8}]})
        self.assertEqual(result["items"][0]["id"], "2")

    def test_context_engine_ranks_contexts(self) -> None:
        engine = ContextEngine()
        result = engine.process({"id": "c1", "content": "context", "relevance": 0.8, "timestamp": 10})
        self.assertEqual(result["contexts"][0]["id"], "c1")

    def test_identity_engine_ranks_entries(self) -> None:
        engine = IdentityEngine()
        result = engine.process({"id": "i1", "content": "identity", "salience": 0.8, "stability": 0.9})
        self.assertEqual(result["entries"][0]["id"], "i1")

    def test_conversation_engine_summarizes_topics(self) -> None:
        engine = ConversationEngine()
        result = engine.process({"id": "t1", "text": "hi", "topic": "greeting"})
        self.assertEqual(result["summary"]["greeting"], 1)

    def test_task_engine_ranks_tasks(self) -> None:
        engine = TaskEngine()
        result = engine.process({"id": "tk1", "title": "deploy", "remaining": 0.2, "deadline": 9999999999})
        self.assertEqual(result["tasks"][0]["id"], "tk1")

    def test_knowledge_engine_consolidates_concepts(self) -> None:
        engine = KnowledgeEngine()
        result = engine.process({"id": "k1", "content": "knowledge", "concepts": ["ai", "memory"], "strength": 0.7})
        self.assertTrue(result["consolidated"])

    def test_graph_engine_traverses_nodes(self) -> None:
        engine = GraphEngine()
        result = engine.process({"node_id": "n1", "edge_to": "n2", "edge_weight": 1.0})
        self.assertEqual(result["traversal"][0], "n2")

    def test_reasoning_engine_infers(self) -> None:
        engine = ReasoningEngine()
        result = engine.process({"id": "r1", "content": "signal", "confidence": 0.7})
        self.assertEqual(result["inference"]["conclusion"], "Observed signal")


if __name__ == "__main__":
    unittest.main()
