from __future__ import annotations

import unittest
from datetime import datetime
from zoneinfo import ZoneInfo

from hanews.models.run import ReportingWindow


class ReportingWindowTests(unittest.TestCase):
    def test_iso_week_bounds_and_archive_name(self) -> None:
        window = ReportingWindow.from_iso_week(2026, 36)
        self.assertEqual(window.start.isoformat(), "2026-08-31")
        self.assertEqual(window.end.isoformat(), "2026-09-06")
        self.assertEqual(window.archive_stem, "2026Week36")

    def test_previous_complete_week_uses_local_monday(self) -> None:
        now = datetime(2026, 8, 10, 8, 0, tzinfo=ZoneInfo("America/Chicago"))
        window = ReportingWindow.previous_complete_week(now=now)
        self.assertEqual(window.start.isoformat(), "2026-08-03")
        self.assertEqual(window.end.isoformat(), "2026-08-09")


if __name__ == "__main__":
    unittest.main()

