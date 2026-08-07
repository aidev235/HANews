from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from hanews.models.item import ResearchEvent
from hanews.models.run import ReportingWindow


@dataclass
class CollectorResult:
    source_name: str
    status: str
    events: list[ResearchEvent] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def log_summary(self) -> dict[str, Any]:
        return {
            "name": self.source_name,
            "status": self.status,
            "candidates": len(self.events),
            "errors": self.errors,
        }


class Collector(ABC):
    name: str

    @abstractmethod
    def collect(self, window: ReportingWindow, retrieved_at: str) -> CollectorResult:
        """Return source events in the reporting window or an explicit failure result."""

