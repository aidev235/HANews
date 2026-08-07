from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
from typing import Iterable

from hanews.models.item import Briefing, ResearchEvent
from hanews.models.run import ReportingWindow, RunRecord
from hanews.pipeline.normalize import valid_http_url


SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9_-]{20,}"),
    re.compile(r"(?i)authorization:\s*bearer\s+\S+"),
    re.compile(r"(?i)OPENAI_API_KEY\s*=\s*\S+"),
]


@dataclass
class ValidationResult:
    checks: dict[str, bool] = field(default_factory=dict)
    errors: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.errors and all(self.checks.values())

    def require(self, name: str, condition: bool, message: str) -> None:
        self.checks[name] = bool(condition)
        if not condition:
            self.errors.append(message)


def _event_dates_in_window(events: Iterable[ResearchEvent], window: ReportingWindow) -> bool:
    for event in events:
        try:
            event_date = date.fromisoformat(event.published_at[:10])
        except ValueError:
            return False
        if not window.start <= event_date <= window.end:
            return False
    return True


def _ordered_urls(markdown: str, heading: str, next_heading: str) -> list[str]:
    try:
        section = markdown.split(heading, 1)[1].split(next_heading, 1)[0]
    except IndexError:
        return []
    return re.findall(r"^\d+\. \[[^\]]+\]\((https?://[^)]+)\)$", section, flags=re.MULTILINE)


def validate_report_bundle(
    *,
    window: ReportingWindow,
    ha_items: list[ResearchEvent],
    general_items: list[ResearchEvent],
    ha_briefings: dict[str, Briefing],
    general_briefings: dict[str, Briefing],
    english_markdown: str,
    chinese_markdown: str,
    limits: dict[str, int],
) -> ValidationResult:
    result = ValidationResult()
    all_events = ha_items + general_items
    result.require(
        "links_are_http_urls",
        all(valid_http_url(event.primary_url) for event in all_events),
        "One or more selected primary URLs are invalid",
    )
    result.require(
        "dates_in_reporting_window",
        _event_dates_in_window(all_events, window),
        "A selected event falls outside the reporting window",
    )
    result.require(
        "ha_count",
        len(ha_items) <= limits["ha"],
        "Harmonic Analysis index exceeds its configured limit",
    )
    result.require(
        "general_count",
        len(general_items) <= limits["general"],
        "General Mathematics index exceeds its configured limit",
    )
    result.require(
        "ha_briefing_count",
        len(ha_briefings) <= limits["ha_briefings"],
        "Harmonic Analysis briefings exceed their configured limit",
    )
    result.require(
        "general_briefing_count",
        len(general_briefings) <= limits["general_briefings"],
        "General Mathematics briefings exceed their configured limit",
    )
    ha_ids = [event.event_id for event in ha_items]
    general_ids = [event.event_id for event in general_items]
    result.require(
        "ha_briefings_are_indexed",
        set(ha_briefings) <= set(ha_ids),
        "A Harmonic Analysis briefing is absent from its index",
    )
    result.require(
        "general_briefings_are_indexed",
        set(general_briefings) <= set(general_ids),
        "A General Mathematics briefing is absent from its index",
    )
    result.require(
        "ha_rank_order",
        all(
            (ha_items[index].rank_score or 0) >= (ha_items[index + 1].rank_score or 0)
            for index in range(max(0, len(ha_items) - 1))
        ),
        "Harmonic Analysis rank order is not descending",
    )
    result.require(
        "general_rank_order",
        all(
            (general_items[index].rank_score or 0)
            >= (general_items[index + 1].rank_score or 0)
            for index in range(max(0, len(general_items) - 1))
        ),
        "General Mathematics rank order is not descending",
    )
    expected_ha_urls = [event.primary_url for event in ha_items]
    expected_general_urls = [event.primary_url for event in general_items]
    english_ha_urls = _ordered_urls(
        english_markdown, "## Harmonic Analysis — Top", "## General Mathematics — Top"
    )
    english_general_urls = _ordered_urls(
        english_markdown, "## General Mathematics — Top", "---"
    )
    chinese_ha_urls = _ordered_urls(
        chinese_markdown, "## 调和分析（Harmonic Analysis）— Top", "## 一般数学（General Mathematics）— Top"
    )
    chinese_general_urls = _ordered_urls(
        chinese_markdown, "## 一般数学（General Mathematics）— Top", "---"
    )
    result.require(
        "english_index_urls",
        english_ha_urls == expected_ha_urls and english_general_urls == expected_general_urls,
        "English rendered index does not match the structured selection",
    )
    result.require(
        "translation_selection_and_links",
        chinese_ha_urls == expected_ha_urls and chinese_general_urls == expected_general_urls,
        "Chinese selection or link order differs from English",
    )
    result.require(
        "no_obvious_secrets",
        not any(pattern.search(english_markdown + chinese_markdown) for pattern in SECRET_PATTERNS),
        "Generated report appears to contain a secret",
    )
    return result


def validate_run_artifacts(record: RunRecord, human_log: Path, structured_log: Path) -> ValidationResult:
    result = ValidationResult()
    data = record.to_dict()
    result.require("human_log_exists", human_log.exists(), "generation.log does not exist")
    result.require("structured_log_exists", structured_log.exists(), "Structured run log does not exist")
    result.require("schema_version", bool(data.get("schema_version")), "schema_version is missing")
    result.require("models_recorded", bool(data.get("models")), "Actual model identifiers are missing")
    result.require("reporting_window", bool(data.get("reporting_window")), "Reporting window missing")
    result.require("statistics", bool(data.get("statistics")), "Pipeline statistics missing")
    result.require("status", bool(data.get("status")), "Final run status missing")
    return result

