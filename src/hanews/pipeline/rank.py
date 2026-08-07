from __future__ import annotations

from hanews.models.item import ResearchEvent


def component_score(event: ResearchEvent, weights: dict[str, float]) -> float:
    event.scores.validate()
    return sum(float(weight) * float(getattr(event.scores, name)) for name, weight in weights.items())


def rank_events(events: list[ResearchEvent], weights: dict[str, float]) -> list[ResearchEvent]:
    for event in events:
        event.rank_score = round(component_score(event, weights), 8)
    return sorted(
        events,
        key=lambda event: (
            -(event.rank_score or 0.0),
            -event.scores.mathematical_importance,
            -event.scores.research_interest,
            -event.scores.confidence,
            event.title.casefold(),
            event.event_id,
        ),
    )


def select_ranked(
    events: list[ResearchEvent],
    *,
    domain: str,
    weights: dict[str, float],
    limit: int,
    minimum_score: float,
) -> list[ResearchEvent]:
    if domain == "harmonic_analysis":
        candidates = [
            event
            for event in events
            if event.coverage == domain
            and event.ha_relationship in {"direct", "strongly_adjacent"}
            and event.scores.harmonic_analysis_relevance >= minimum_score
        ]
    elif domain == "general_mathematics":
        candidates = [
            event
            for event in events
            if event.coverage == domain
            and event.scores.mathematical_importance >= minimum_score
        ]
    else:
        raise ValueError(f"Unknown ranking domain: {domain}")
    return rank_events(candidates, weights)[:limit]

