from __future__ import annotations

import unittest

from hanews.models.run import ReportingWindow
from hanews.pipeline.deduplicate import deduplicate_events
from hanews.pipeline.normalize import normalize_doi, normalize_event
from tests.helpers import make_event


class NormalizeAndDeduplicateTests(unittest.TestCase):
    def test_doi_normalization(self) -> None:
        self.assertEqual(normalize_doi("https://doi.org/10.1000/ABC"), "10.1000/abc")
        self.assertEqual(normalize_doi("doi: 10.1000/ABC"), "10.1000/abc")

    def test_normalization_recomputes_stable_identity(self) -> None:
        event = make_event(title="  A   restriction theorem  ")
        normalized = normalize_event(event, ReportingWindow.from_iso_week(2026, 32))
        self.assertEqual(normalized.title, "A restriction theorem")
        self.assertTrue(normalized.canonical_id.startswith("arxiv:"))
        self.assertEqual(len(normalized.event_id), 24)

    def test_same_work_same_event_merges_provenance(self) -> None:
        left = make_event(event_id="a")
        right = make_event(event_id="b")
        right.source_name = "mirror"
        right.primary_url = "https://example.edu/paper"
        right.provenance = [
            {"source_name": "mirror", "primary_url": right.primary_url, "retrieved_at": "now"}
        ]
        result = deduplicate_events([left, right])
        self.assertEqual(len(result), 1)
        self.assertEqual(len(result[0].provenance), 2)

    def test_different_event_types_are_not_merged(self) -> None:
        preprint = make_event(item_type="NEW_PREPRINT")
        publication = make_event(item_type="JOURNAL_PUBLICATION", event_id="publication")
        result = deduplicate_events([preprint, publication])
        self.assertEqual(len(result), 2)


if __name__ == "__main__":
    unittest.main()

