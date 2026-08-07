from __future__ import annotations

from datetime import datetime, timezone

from hanews.models.item import ResearchEvent, ScoreComponents


def make_event(
    *,
    title: str = "A restriction theorem",
    event_id: str = "event-1",
    canonical_id: str = "work-1",
    published_at: str = "2026-08-04T12:00:00+00:00",
    item_type: str = "NEW_PREPRINT",
    arxiv_id: str | None = "2608.00001",
    doi: str | None = None,
    coverage: str = "harmonic_analysis",
    relationship: str = "direct",
    importance: float = 0.8,
    relevance: float = 0.9,
) -> ResearchEvent:
    return ResearchEvent(
        canonical_id=canonical_id,
        event_id=event_id,
        title=title,
        authors=["Ada Analyst"],
        abstract="We establish a carefully stated result from verified source metadata.",
        item_type=item_type,
        source_name="arxiv",
        primary_url=f"https://arxiv.org/abs/{arxiv_id or '2608.00001'}",
        discovery_url="https://export.arxiv.org/api/query",
        published_at=published_at,
        updated_at=published_at,
        discovered_at=datetime.now(timezone.utc).isoformat(),
        doi=doi,
        arxiv_id=arxiv_id,
        categories=["math.CA"],
        topics=["Fourier restriction"],
        coverage=coverage,
        ha_relationship=relationship,
        scores=ScoreComponents(
            harmonic_analysis_relevance=relevance,
            mathematical_importance=importance,
            novelty=0.7,
            timeliness=0.9,
            source_reliability=0.95,
            research_interest=0.75,
            confidence=0.8,
        ),
        provenance=[
            {
                "source_name": "arxiv",
                "primary_url": f"https://arxiv.org/abs/{arxiv_id or '2608.00001'}",
                "retrieved_at": datetime.now(timezone.utc).isoformat(),
            }
        ],
    )

