from __future__ import annotations

import hashlib
import re
import unicodedata
from dataclasses import asdict, dataclass, field
from typing import Any


SCORE_FIELDS = (
    "harmonic_analysis_relevance",
    "mathematical_importance",
    "novelty",
    "timeliness",
    "source_reliability",
    "research_interest",
    "confidence",
)


def normalized_title_key(title: str) -> str:
    normalized = unicodedata.normalize("NFKC", title).casefold()
    return re.sub(r"[^\w]+", " ", normalized, flags=re.UNICODE).strip()


def stable_digest(*parts: str, length: int = 24) -> str:
    payload = "\x1f".join(parts).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()[:length]


@dataclass
class ScoreComponents:
    harmonic_analysis_relevance: float = 0.0
    mathematical_importance: float = 0.0
    novelty: float = 0.0
    timeliness: float = 0.0
    source_reliability: float = 0.0
    research_interest: float = 0.0
    confidence: float = 0.0

    def validate(self) -> None:
        for name in SCORE_FIELDS:
            value = float(getattr(self, name))
            if not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be between 0 and 1; got {value}")

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> ScoreComponents:
        score = cls(**{name: float(value.get(name, 0.0)) for name in SCORE_FIELDS})
        score.validate()
        return score


@dataclass
class ResearchEvent:
    canonical_id: str
    event_id: str
    title: str
    authors: list[str]
    abstract: str
    item_type: str
    source_name: str
    primary_url: str
    discovery_url: str | None
    published_at: str
    updated_at: str | None
    discovered_at: str
    doi: str | None = None
    arxiv_id: str | None = None
    categories: list[str] = field(default_factory=list)
    topics: list[str] = field(default_factory=list)
    other_urls: list[str] = field(default_factory=list)
    coverage: str = "exclude"
    ha_relationship: str = "unrelated"
    scores: ScoreComponents = field(default_factory=ScoreComponents)
    rank_score: float | None = None
    assessment_rationale: str = ""
    provenance: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> ResearchEvent:
        data = dict(value)
        data["scores"] = ScoreComponents.from_dict(data.get("scores", {}))
        return cls(**data)

    @staticmethod
    def identity(
        *, title: str, authors: list[str], arxiv_id: str | None, doi: str | None
    ) -> str:
        if arxiv_id:
            return f"arxiv:{arxiv_id.casefold()}"
        if doi:
            return f"doi:{doi.casefold()}"
        author_key = "|".join(sorted(name.casefold().strip() for name in authors))
        return f"title:{stable_digest(normalized_title_key(title), author_key)}"

    @staticmethod
    def event_identity(canonical_id: str, item_type: str, event_date: str) -> str:
        return stable_digest(canonical_id, item_type, event_date)


@dataclass
class Briefing:
    event_id: str
    brief: str
    why_it_matters: str
    connections: str = ""

    def to_dict(self) -> dict[str, str]:
        return asdict(self)


@dataclass
class TranslatedBriefing:
    event_id: str
    title: str
    topics: list[str]
    brief: str
    why_it_matters: str
    connections: str = ""

