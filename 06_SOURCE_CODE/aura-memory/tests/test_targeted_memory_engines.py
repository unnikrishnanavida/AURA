from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.append(str(ROOT))

from working_memory.engine import Engine as WorkingMemoryEngine
from short_term_memory.engine import Engine as ShortTermEngine
from long_term_memory.engine import Engine as LongTermEngine
from retrieval.retrieval_engine import RetrievalEngine
from search.search_engine import SearchEngine


class TargetedMemoryEnginesTestCase(unittest.TestCase):
    def test_working_memory_rehearsal_increases_activation(self) -> None:
        engine = WorkingMemoryEngine({"capacity": 4})
        engine.start()
        payload = {"id": "a", "content": "alpha", "importance": 0.9}
        engine.process(payload)
        before = engine.rehearse("a")
        self.assertGreater(before["activation"], 0.0)
        engine.shutdown()

    def test_short_term_memory_decay_and_rehearsal(self) -> None:
        engine = ShortTermEngine({"decay_rate": 0.01})
        engine.process({"id": "s1", "content": "beta", "strength": 0.8})
        rehearse_result = engine.rehearse("s1")
        self.assertGreater(rehearse_result["strength"], 0.8)

    def test_long_term_memory_consolidation(self) -> None:
        engine = LongTermEngine({"retention_threshold": 0.4})
        result = engine.process({"id": "l1", "content": "gamma", "importance": 0.6})
        self.assertTrue(result["items"][0]["consolidated"])

    def test_retrieval_ranks_candidates(self) -> None:
        engine = RetrievalEngine()
        result = engine.process({
            "query": "alpha",
            "candidates": [
                {"id": "1", "content": "beta", "context_score": 0.1},
                {"id": "2", "content": "alpha memory", "context_score": 0.8},
            ],
        })
        self.assertEqual(result["results"][0]["id"], "2")

    def test_search_ranks_documents(self) -> None:
        engine = SearchEngine()
        result = engine.process({
            "query": "alpha",
            "documents": [
                {"id": "1", "content": "beta gamma"},
                {"id": "2", "content": "alpha beta alpha"},
            ],
        })
        self.assertEqual(result["results"][0]["id"], "2")


if __name__ == "__main__":
    unittest.main()
