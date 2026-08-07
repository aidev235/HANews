from __future__ import annotations

import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from hanews.models.item import Briefing, TranslatedBriefing
from hanews.models.run import ReportingWindow
from hanews.pipeline.validate import validate_report_bundle
from hanews.reporting.archive import ArchiveManager
from hanews.reporting.weekly import render_chinese_report, render_english_report
from tests.helpers import make_event


class ReportingAndArchiveTests(unittest.TestCase):
    def test_english_chinese_link_parity(self) -> None:
        window = ReportingWindow.from_iso_week(2026, 32)
        event = make_event()
        event.rank_score = 0.88
        briefing = Briefing(event.event_id, "Brief.", "Important.", "Connection.")
        translations = {
            event.event_id: TranslatedBriefing(
                event.event_id,
                "一个限制性定理",
                ["傅里叶限制（Fourier restriction）"],
                "简报。",
                "重要。",
                "关联。",
            )
        }
        now = datetime(2026, 8, 10, 8, tzinfo=ZoneInfo("America/Chicago"))
        english = render_english_report(
            window=window,
            generated_at=now,
            timezone="America/Chicago",
            model_label="test",
            ha_items=[event],
            general_items=[],
            ha_briefings={event.event_id: briefing},
            general_briefings={},
            configured_ha_count=20,
            configured_general_count=8,
        )
        chinese = render_chinese_report(
            window=window,
            generated_at=now,
            timezone="America/Chicago",
            model_label="test",
            ha_items=[event],
            general_items=[],
            ha_briefings={event.event_id: briefing},
            general_briefings={},
            translations=translations,
            configured_ha_count=20,
            configured_general_count=8,
        )
        result = validate_report_bundle(
            window=window,
            ha_items=[event],
            general_items=[],
            ha_briefings={event.event_id: briefing},
            general_briefings={},
            english_markdown=english,
            chinese_markdown=chinese,
            limits={"ha": 20, "general": 8, "ha_briefings": 5, "general_briefings": 3},
        )
        self.assertTrue(result.ok, result.errors)

    def test_archive_is_idempotent_and_preserves_changed_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            manager = ArchiveManager(root, "archive", True)
            window = ReportingWindow.from_iso_week(2026, 32)
            first_en, _ = manager.write_week(window, "first\n", "第一\n")
            second_en, _ = manager.write_week(window, "first\n", "第一\n")
            third_en, _ = manager.write_week(window, "second\n", "第二\n")
            self.assertEqual(first_en.status, "created")
            self.assertEqual(second_en.status, "unchanged")
            self.assertEqual(third_en.status, "updated")
            self.assertEqual(len(third_en.revisions_created), 1)
            self.assertEqual(third_en.revisions_created[0].read_text(), "first\n")


if __name__ == "__main__":
    unittest.main()

