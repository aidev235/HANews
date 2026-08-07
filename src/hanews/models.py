"""Typed domain records. Authoritative values and normalized matching keys are separate."""
from __future__ import annotations

from datetime import date, datetime
from enum import StrEnum
from typing import Any
from pydantic import BaseModel, ConfigDict, Field

class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=False)

class EventType(StrEnum):
    NEW_PREPRINT="NEW_PREPRINT"; MAJOR_REVISION="MAJOR_REVISION"; JOURNAL_PUBLICATION="JOURNAL_PUBLICATION"
class Relevance(StrEnum):
    DIRECT_HA="direct_ha"; STRONGLY_ADJACENT="strongly_adjacent"; SUPERFICIAL="superficial"; UNRELATED="unrelated"

class Provenance(StrictModel):
    source: str; retrieved_at: datetime; source_url: str; snapshot: dict[str, Any] = Field(default_factory=dict)
class WorkIdentity(StrictModel):
    canonical_id: str; arxiv_id: str|None=None; doi: str|None=None; correspondence: list[str]=Field(default_factory=list)
class ResearchEvent(StrictModel):
    event_id: str; event_type: EventType; work: WorkIdentity; title: str; authors: list[str]
    url: str; occurred_at: datetime; provenance: list[Provenance]; normalized: dict[str, Any]=Field(default_factory=dict)
class RankingComponents(StrictModel):
    topical_relevance: float=0; significance: float=0; novelty: float=0; breadth: float=0; source_confidence: float=0
    final_score: float|None=None
class ReportingWindow(StrictModel):
    start: date; end: date; timezone: str; iso_year: int; iso_week: int
class ModelInvocation(StrictModel):
    task: str; requested_model: str; actual_model: str; fallback_reason: str|None=None; timestamp: datetime
class SourceResult(StrictModel):
    source: str; ok: bool; items: list[ResearchEvent]=Field(default_factory=list); attempts: int=1; error: str|None=None
class ValidationResult(StrictModel):
    name: str; passed: bool; message: str=""
class RunRecord(StrictModel):
    schema_version: str="1.0"; run_id: str; started_at: datetime; updated_at: datetime; timezone: str
    reporting_window: ReportingWindow; trigger: str; stage: str="initialize"; models: list[ModelInvocation]=Field(default_factory=list)
    sources: list[SourceResult]=Field(default_factory=list); statistics: dict[str,int]=Field(default_factory=dict)
    outputs: list[str]=Field(default_factory=list); validation: list[ValidationResult]=Field(default_factory=list)
    warnings: list[str]=Field(default_factory=list); errors: list[str]=Field(default_factory=list); failed_stage: str|None=None
    git: dict[str,Any]=Field(default_factory=dict); status: str="running"
