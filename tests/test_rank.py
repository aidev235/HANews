from __future__ import annotations

import unittest

from hanews.pipeline.rank import rank_events, select_ranked
from tests.helpers import make_event


WEIGHTS = {
    "harmonic_analysis_relevance": 0.4,
    "mathematical_importance": 0.3,
    "novelty": 0.1,
    "timeliness": 0.05,
    "source_reliability": 0.05,
    "research_interest": 0.05,
    "confidence": 0.05,
}


class RankingTests(unittest.TestCase):
    def test_deterministic_descending_order(self) -> None:
        strong = make_event(title="Strong", event_id="strong", importance=0.9, relevance=0.95)
        weak = make_event(title="Weak", event_id="weak", importance=0.5, relevance=0.6)
        ranked = rank_events([weak, strong], WEIGHTS)
        self.assertEqual([event.event_id for event in ranked], ["strong", "weak"])
        self.assertGreaterEqual(ranked[0].rank_score or 0, ranked[1].rank_score or 0)

    def test_threshold_is_not_quota_filling(self) -> None:
        weak = make_event(relevance=0.2)
        selected = select_ranked(
            [weak],
            domain="harmonic_analysis",
            weights=WEIGHTS,
            limit=20,
            minimum_score=0.55,
        )
        self.assertEqual(selected, [])


if __name__ == "__main__":
    unittest.main()

