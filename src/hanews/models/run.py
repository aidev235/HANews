from __future__ import annotations

import hashlib
import os
import time
from dataclasses import asdict, dataclass, field
from datetime import date, datetime, timedelta
from typing import Any
from zoneinfo import ZoneInfo


@dataclass(frozen=True)
class ReportingWindow:
    start: date
    end: date
    iso_year: int
    iso_week: int

    @classmethod
    def from_iso_week(cls, year: int, week: int) -> ReportingWindow:
        start = date.fromisocalendar(year, week, 1)
        end = date.fromisocalendar(year, week, 7)
        return cls(start=start, end=end, iso_year=year, iso_week=week)

    @classmethod
    def previous_complete_week(
        cls, *, now: datetime | None = None, timezone: str = "America/Chicago"
    ) -> ReportingWindow:
        zone = ZoneInfo(timezone)
        local_now = now.astimezone(zone) if now else datetime.now(zone)
        current_monday = local_now.date() - timedelta(days=local_now.weekday())
        end = current_monday - timedelta(days=1)
        start = end - timedelta(days=6)
        iso = start.isocalendar()
        return cls(start=start, end=end, iso_year=iso.year, iso_week=iso.week)

    @property
    def archive_stem(self) -> str:
        return f"{self.iso_year}Week{self.iso_week:02d}"

    def to_dict(self) -> dict[str, Any]:
        return {
            "start": self.start.isoformat(),
            "end": self.end.isoformat(),
            "iso_year": self.iso_year,
            "iso_week": self.iso_week,
        }


def new_run_id(started_at: datetime) -> str:
    seed = f"{started_at.isoformat()}:{os.getpid()}:{time.time_ns()}"
    return hashlib.sha256(seed.encode("utf-8")).hexdigest()[:12]


@dataclass
class RunRecord:
    schema_version: int
    run_id: str
    project: str
    started_at: str
    timezone: str
    reporting_window: dict[str, Any]
    trigger: dict[str, Any]
    finished_at: str | None = None
    stage: str = "initializing"
    models: list[dict[str, Any]] = field(default_factory=list)
    sources: list[dict[str, Any]] = field(default_factory=list)
    statistics: dict[str, int] = field(default_factory=dict)
    outputs: dict[str, str] = field(default_factory=dict)
    validation: dict[str, Any] = field(
        default_factory=lambda: {"status": "pending", "checks": {}}
    )
    warnings: list[str] = field(default_factory=list)
    errors: list[dict[str, str]] = field(default_factory=list)
    git: dict[str, Any] = field(
        default_factory=lambda: {
            "commit_attempted": False,
            "commit_success": False,
            "commit_hash": None,
            "commit_message": None,
            "push_attempted": False,
            "push_success": False,
            "remote": None,
            "branch": None,
            "metadata_commit": None,
        }
    )
    files_created: list[str] = field(default_factory=list)
    files_modified: list[str] = field(default_factory=list)
    status: str = "running"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

