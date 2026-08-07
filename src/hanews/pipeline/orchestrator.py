from __future__ import annotations

import json
import os
from datetime import date, datetime
from pathlib import Path
from typing import Any
from zoneinfo import ZoneInfo

from hanews.collectors.arxiv import build_collectors
from hanews.collectors.base import Collector
from hanews.config import AppConfig
from hanews.git.repository import GitRepository
from hanews.llm.client import LLMClient, LLMResponse
from hanews.llm.tasks import classify_events, summarize_events, translate_briefings
from hanews.models.item import ResearchEvent
from hanews.models.run import ReportingWindow, RunRecord, new_run_id
from hanews.pipeline.deduplicate import deduplicate_events
from hanews.pipeline.normalize import normalize_events
from hanews.pipeline.rank import select_ranked
from hanews.pipeline.validate import validate_report_bundle, validate_run_artifacts
from hanews.reporting.archive import ArchiveManager, ArchiveWriteResult
from hanews.reporting.weekly import render_chinese_report, render_english_report
from hanews.storage.atomic import atomic_write_text
from hanews.storage.items import ItemStore
from hanews.storage.run_log import DualRunLogger


class GenerationPipeline:
    def __init__(
        self,
        config: AppConfig,
        llm_client: LLMClient,
        collectors: list[Collector] | None = None,
    ) -> None:
        self.config = config
        self.llm_client = llm_client
        self.collectors = collectors or build_collectors(
            config.sources, config.raw.get("network", {})
        )

    def _model_log(self, record: RunRecord, task: str, response: LLMResponse) -> None:
        matching = next(
            (
                value
                for value in record.models
                if value.get("task") == task
                and value.get("actual_model") == response.actual_model
                and value.get("requested_model") == response.requested_model
            ),
            None,
        )
        if matching:
            matching["calls"] = int(matching.get("calls", 1)) + 1
            return
        value = response.model_log(task)
        value["calls"] = 1
        record.models.append(value)

    @staticmethod
    def _trigger() -> dict[str, Any]:
        if os.getenv("GITHUB_ACTIONS") == "true":
            return {
                "type": "github_actions",
                "workflow": os.getenv("GITHUB_WORKFLOW", "weekly"),
                "run_id": os.getenv("GITHUB_RUN_ID"),
            }
        return {"type": "cli"}

    def _new_record(self, window: ReportingWindow, started: datetime) -> RunRecord:
        logging = self.config.raw["logging"]
        ranker = self.config.models["ranker"]
        return RunRecord(
            schema_version=int(logging["schema_version"]),
            run_id=new_run_id(started),
            project=str(self.config.raw["project"]["name"]),
            started_at=started.isoformat(),
            timezone=self.config.timezone,
            reporting_window=window.to_dict(),
            trigger=self._trigger(),
            models=[
                {
                    "task": "ranking",
                    "provider": ranker.provider,
                    "requested_model": ranker.model,
                    "actual_model": ranker.model,
                    "configuration": {
                        "harmonic_analysis_weights": self.config.ranking[
                            "harmonic_analysis"
                        ],
                        "general_mathematics_weights": self.config.ranking[
                            "general_mathematics"
                        ],
                    },
                    "calls": 1,
                }
            ],
        )

    @staticmethod
    def _is_in_window(event: ResearchEvent, window: ReportingWindow) -> bool:
        try:
            published = date.fromisoformat(event.published_at[:10])
        except ValueError:
            return False
        return window.start <= published <= window.end

    @staticmethod
    def _track_write(record: RunRecord, root: Path, path: Path, content: str) -> None:
        existed = path.exists()
        old = path.read_text(encoding="utf-8") if existed else None
        atomic_write_text(path, content)
        relative = path.relative_to(root).as_posix()
        if not existed:
            record.files_created.append(relative)
        elif old != content:
            record.files_modified.append(relative)

    @staticmethod
    def _track_archive(
        record: RunRecord, root: Path, result: ArchiveWriteResult
    ) -> list[Path]:
        relative = result.path.relative_to(root).as_posix()
        if result.status == "created":
            record.files_created.append(relative)
        elif result.status == "updated":
            record.files_modified.append(relative)
            record.warnings.append(
                f"Updated {relative}; the prior content was retained as a content-addressed revision"
            )
        for revision in result.revisions_created:
            record.files_created.append(revision.relative_to(root).as_posix())
        return [result.path, *result.revisions_created]

    def run(self, window: ReportingWindow, *, publish_git: bool = True) -> RunRecord:
        zone = ZoneInfo(self.config.timezone)
        started = datetime.now(zone)
        record = self._new_record(window, started)
        human_path = self.config.path(self.config.raw["logging"]["human_log"])
        structured_dir = self.config.path(
            self.config.raw["logging"]["structured_log_dir"]
        )
        logger = DualRunLogger(human_path, structured_dir, record)
        logger.start()
        generated_paths: list[Path] = [human_path, logger.json_path]
        finalized_once = False

        try:
            logger.checkpoint("collect")
            raw_events: list[ResearchEvent] = []
            successful_sources = 0
            for collector in self.collectors:
                result = collector.collect(window, started.isoformat())
                record.sources.append(result.log_summary())
                raw_events.extend(result.events)
                if result.status == "success":
                    successful_sources += 1
                else:
                    record.warnings.append(
                        f"Source {result.source_name} failed: {'; '.join(result.errors)}"
                    )
                logger.checkpoint()
            if not successful_sources:
                raise RuntimeError("Every enabled source failed")
            record.statistics["raw_candidates"] = len(raw_events)

            logger.checkpoint("normalize")
            in_window = [event for event in raw_events if self._is_in_window(event, window)]
            excluded = len(raw_events) - len(in_window)
            if excluded:
                record.warnings.append(f"Excluded {excluded} source items outside the reporting window")
            normalized = normalize_events(in_window, window)
            record.statistics["normalized_candidates"] = len(normalized)

            logger.checkpoint("deduplicate")
            events = deduplicate_events(normalized)
            record.statistics["deduplicated_candidates"] = len(events)

            logger.checkpoint("classify")
            if events:
                classification_responses = classify_events(
                    self.llm_client,
                    self.config.models["classifier"],
                    events,
                    root=self.config.root,
                    topics=self.config.topics,
                )
                for response in classification_responses:
                    self._model_log(record, "classification", response)
            record.statistics["ha_relevant_candidates"] = sum(
                event.coverage == "harmonic_analysis" for event in events
            )
            record.statistics["general_math_candidates"] = sum(
                event.coverage == "general_mathematics" for event in events
            )

            logger.checkpoint("rank")
            report_config = self.config.raw["report"]
            ha_items = select_ranked(
                events,
                domain="harmonic_analysis",
                weights=self.config.ranking["harmonic_analysis"],
                limit=int(report_config["harmonic_analysis_count"]),
                minimum_score=float(report_config["minimum_ha_relevance"]),
            )
            general_items = select_ranked(
                events,
                domain="general_mathematics",
                weights=self.config.ranking["general_mathematics"],
                limit=int(report_config["general_math_count"]),
                minimum_score=float(report_config["minimum_general_importance"]),
            )
            ha_detail_items = ha_items[: int(report_config["harmonic_analysis_briefing_count"])]
            general_detail_items = general_items[: int(report_config["general_math_briefing_count"])]
            detail_items = ha_detail_items + general_detail_items

            logger.checkpoint("summarize")
            briefings, summary_response = summarize_events(
                self.llm_client,
                self.config.models["summarizer"],
                detail_items,
                root=self.config.root,
            )
            if summary_response:
                self._model_log(record, "summarization", summary_response)
            ha_briefings = {
                event.event_id: briefings[event.event_id]
                for event in ha_detail_items
                if event.event_id in briefings
            }
            general_briefings = {
                event.event_id: briefings[event.event_id]
                for event in general_detail_items
                if event.event_id in briefings
            }

            generated_at = datetime.now(zone)
            english_model_label = "; ".join(
                f"{value['task']}={value['actual_model']}" for value in record.models
            )
            english = render_english_report(
                window=window,
                generated_at=generated_at,
                timezone=self.config.timezone,
                model_label=english_model_label,
                ha_items=ha_items,
                general_items=general_items,
                ha_briefings=ha_briefings,
                general_briefings=general_briefings,
                configured_ha_count=int(report_config["harmonic_analysis_count"]),
                configured_general_count=int(report_config["general_math_count"]),
            )

            logger.checkpoint("translate_zh")
            selected_items = ha_items + general_items
            translations, translation_response = translate_briefings(
                self.llm_client,
                self.config.models["translator"],
                selected_items,
                briefings,
                root=self.config.root,
            )
            if translation_response:
                self._model_log(record, "translation_zh", translation_response)
            translation_model_label = (
                translation_response.actual_model if translation_response else "not invoked"
            )
            chinese = render_chinese_report(
                window=window,
                generated_at=generated_at,
                timezone=self.config.timezone,
                model_label=translation_model_label,
                ha_items=ha_items,
                general_items=general_items,
                ha_briefings=ha_briefings,
                general_briefings=general_briefings,
                translations=translations,
                configured_ha_count=int(report_config["harmonic_analysis_count"]),
                configured_general_count=int(report_config["general_math_count"]),
            )

            logger.checkpoint("validate")
            validation = validate_report_bundle(
                window=window,
                ha_items=ha_items,
                general_items=general_items,
                ha_briefings=ha_briefings,
                general_briefings=general_briefings,
                english_markdown=english,
                chinese_markdown=chinese,
                limits={
                    "ha": int(report_config["harmonic_analysis_count"]),
                    "general": int(report_config["general_math_count"]),
                    "ha_briefings": int(report_config["harmonic_analysis_briefing_count"]),
                    "general_briefings": int(report_config["general_math_briefing_count"]),
                },
            )
            record.validation = {
                "status": "success" if validation.ok else "failed",
                "checks": validation.checks,
                "errors": validation.errors,
            }
            if not validation.ok:
                raise ValueError("Report validation failed: " + "; ".join(validation.errors))

            logger.checkpoint("write_outputs")
            archive_config = self.config.raw["archive"]
            archive = ArchiveManager(
                self.config.root,
                str(archive_config["directory"]),
                bool(archive_config.get("preserve_changed_revisions", True)),
            )
            english_archive, chinese_archive = archive.write_week(window, english, chinese)
            generated_paths.extend(self._track_archive(record, self.config.root, english_archive))
            generated_paths.extend(self._track_archive(record, self.config.root, chinese_archive))
            latest_english = self.config.root / "latest-week.md"
            latest_chinese = self.config.root / "latest-week-zh.md"
            self._track_write(record, self.config.root, latest_english, english)
            self._track_write(record, self.config.root, latest_chinese, chinese)
            generated_paths.extend([latest_english, latest_chinese])

            item_path = self.config.path(self.config.raw["storage"]["items_file"])
            item_existed = item_path.exists()
            item_store = ItemStore(item_path)
            appended = item_store.append_changed(events)
            if appended:
                relative = item_path.relative_to(self.config.root).as_posix()
                (record.files_modified if item_existed else record.files_created).append(relative)
                generated_paths.append(item_path)

            state_path = self.config.path(self.config.raw["storage"]["state_file"])
            state = {
                "schema_version": 1,
                "last_successful_run_id": record.run_id,
                "reporting_window": window.to_dict(),
                "finished_at": datetime.now(zone).isoformat(),
                "selected_event_ids": [event.event_id for event in selected_items],
            }
            self._track_write(
                record,
                self.config.root,
                state_path,
                json.dumps(state, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
            )
            generated_paths.append(state_path)

            record.statistics.update(
                {
                    "ha_selected": len(ha_items),
                    "general_math_selected": len(general_items),
                    "ha_briefings": len(ha_briefings),
                    "general_math_briefings": len(general_briefings),
                    "item_versions_appended": appended,
                }
            )
            record.outputs.update(
                {
                    "english_report": "latest-week.md",
                    "chinese_report": "latest-week-zh.md",
                    "english_archive": english_archive.path.relative_to(
                        self.config.root
                    ).as_posix(),
                    "chinese_archive": chinese_archive.path.relative_to(
                        self.config.root
                    ).as_posix(),
                    "english_status": "success",
                    "chinese_status": "success",
                }
            )

            record.stage = "reports_complete"
            finished = datetime.now(zone)
            logger.finalize(status="success", finished_at=finished.isoformat())
            finalized_once = True
            artifact_validation = validate_run_artifacts(record, human_path, logger.json_path)
            if not artifact_validation.ok:
                raise ValueError(
                    "Run artifact validation failed: " + "; ".join(artifact_validation.errors)
                )

            if publish_git and bool(self.config.raw["git"].get("auto_commit", True)):
                record.stage = "git_publish"
                logger.checkpoint()
                repository = GitRepository(self.config.root, self.config.raw["git"])
                repository.publish(
                    record=record,
                    logger=logger,
                    generated_paths=generated_paths,
                )
            return record
        except BaseException as exc:
            logger.record_error(record.stage, exc)
            record.validation["status"] = "failed"
            if finalized_once:
                record.warnings.append("A failure occurred after local reports were finalized")
            logger.finalize(status="failed", finished_at=datetime.now(zone).isoformat())
            raise
