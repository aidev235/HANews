from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from hanews.models.run import RunRecord
from hanews.storage.atomic import atomic_write_text


class DualRunLogger:
    """Maintains an append-only human log and an authoritative atomic JSON record."""

    def __init__(self, human_path: Path, structured_dir: Path, record: RunRecord) -> None:
        self.human_path = human_path
        self.structured_dir = structured_dir
        self.record = record
        timestamp = datetime.fromisoformat(record.started_at).strftime("%Y-%m-%dT%H%M%S%z")
        self.json_path = structured_dir / f"{timestamp}_{record.run_id}.json"

    def start(self) -> None:
        self.human_path.parent.mkdir(parents=True, exist_ok=True)
        self.structured_dir.mkdir(parents=True, exist_ok=True)
        self._write_json()
        self._append(
            "\n".join(
                [
                    f"===== RUN {self.record.run_id} START =====",
                    f"started_at: {self.record.started_at}",
                    f"timezone: {self.record.timezone}",
                    "reporting_window: "
                    f"{self.record.reporting_window['start']} -- "
                    f"{self.record.reporting_window['end']}",
                    f"trigger: {self.record.trigger.get('type', 'unknown')}",
                    "status: running",
                    f"===== RUN {self.record.run_id} START RECORDED =====",
                ]
            )
        )

    def checkpoint(self, stage: str | None = None) -> None:
        if stage:
            self.record.stage = stage
        self._write_json()

    def finalize(self, *, status: str, finished_at: str) -> None:
        self.record.status = status
        self.record.finished_at = finished_at
        self._write_json()
        stats = self.record.statistics
        sources = self.record.sources
        models = ", ".join(
            f"{m.get('task')}={m.get('actual_model', m.get('model'))}"
            for m in self.record.models
        ) or "none"
        source_summary = ", ".join(
            f"{source.get('name')}:{source.get('status')}({source.get('candidates', 0)})"
            for source in sources
        ) or "none"
        lines = [
            f"===== RUN {self.record.run_id} FINAL =====",
            f"finished_at: {finished_at}",
            f"status: {status}",
            f"stage: {self.record.stage}",
            f"models: {models}",
            f"sources: {source_summary}",
            f"raw_candidates: {stats.get('raw_candidates', 0)}",
            f"normalized_candidates: {stats.get('normalized_candidates', 0)}",
            f"deduplicated_candidates: {stats.get('deduplicated_candidates', 0)}",
            f"ha_relevant_candidates: {stats.get('ha_relevant_candidates', 0)}",
            f"general_math_candidates: {stats.get('general_math_candidates', 0)}",
            f"ha_selected: {stats.get('ha_selected', 0)}",
            f"general_math_selected: {stats.get('general_math_selected', 0)}",
            f"ha_briefings: {stats.get('ha_briefings', 0)}",
            f"general_math_briefings: {stats.get('general_math_briefings', 0)}",
            f"english_report_status: {self.record.outputs.get('english_status', 'not_created')}",
            f"chinese_translation_status: {self.record.outputs.get('chinese_status', 'not_created')}",
            f"validation_status: {self.record.validation.get('status', 'pending')}",
            f"archives: {self.record.outputs.get('english_archive', '-')}, "
            f"{self.record.outputs.get('chinese_archive', '-')}",
            f"files_created: {', '.join(self.record.files_created) or 'none'}",
            f"files_modified: {', '.join(self.record.files_modified) or 'none'}",
            f"warnings: {json.dumps(self.record.warnings, ensure_ascii=False)}",
            f"errors: {json.dumps(self.record.errors, ensure_ascii=False)}",
            f"git_commit_status: {self.record.git.get('commit_success')}",
            f"git_commit_hash: {self.record.git.get('commit_hash')}",
            f"git_push_status: {self.record.git.get('push_success')}",
            f"structured_log: {self.json_path.as_posix()}",
            f"===== RUN {self.record.run_id} END =====",
        ]
        self._append("\n".join(lines))

    def record_error(self, stage: str, exc: BaseException) -> None:
        self.record.stage = stage
        self.record.errors.append(
            {"stage": stage, "type": type(exc).__name__, "message": str(exc)}
        )
        self._write_json()

    def append_git_result(self, message: str) -> None:
        self._write_json()
        self._append(
            "\n".join(
                [
                    f"===== RUN {self.record.run_id} GIT RESULT =====",
                    f"message: {message}",
                    f"commit_attempted: {self.record.git.get('commit_attempted')}",
                    f"commit_success: {self.record.git.get('commit_success')}",
                    f"report_commit_hash: {self.record.git.get('commit_hash')}",
                    f"push_attempted: {self.record.git.get('push_attempted')}",
                    f"report_push_success: {self.record.git.get('push_success')}",
                    f"remote: {self.record.git.get('remote')}",
                    f"branch: {self.record.git.get('branch')}",
                    f"===== RUN {self.record.run_id} GIT RESULT END =====",
                ]
            )
        )

    def _write_json(self) -> None:
        atomic_write_text(
            self.json_path,
            json.dumps(self.record.to_dict(), ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        )

    def _append(self, block: str) -> None:
        with self.human_path.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(block.rstrip() + "\n")
            handle.flush()
