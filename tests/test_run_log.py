from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from hanews.models.run import ReportingWindow, RunRecord
from hanews.storage.run_log import DualRunLogger


class RunLogTests(unittest.TestCase):
    def test_failed_run_is_kept_in_both_logs(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            started = datetime(2026, 8, 10, 8, tzinfo=ZoneInfo("America/Chicago"))
            record = RunRecord(
                schema_version=1,
                run_id="run123",
                project="HANews",
                started_at=started.isoformat(),
                timezone="America/Chicago",
                reporting_window=ReportingWindow.from_iso_week(2026, 32).to_dict(),
                trigger={"type": "test"},
            )
            logger = DualRunLogger(root / "generation.log", root / "runs", record)
            logger.start()
            error = RuntimeError("source failed")
            logger.record_error("collect", error)
            logger.finalize(status="failed", finished_at=started.isoformat())
            data = json.loads(logger.json_path.read_text())
            self.assertEqual(data["status"], "failed")
            self.assertEqual(data["errors"][0]["stage"], "collect")
            human = (root / "generation.log").read_text()
            self.assertIn("RUN run123 START", human)
            self.assertIn("status: failed", human)


if __name__ == "__main__":
    unittest.main()

