from __future__ import annotations

from hanews.models.item import ResearchEvent, normalized_title_key


def _author_keys(event: ResearchEvent) -> set[str]:
    return {" ".join(author.casefold().split()) for author in event.authors}


def _same_work(left: ResearchEvent, right: ResearchEvent) -> bool:
    if left.arxiv_id and right.arxiv_id and left.arxiv_id.casefold() == right.arxiv_id.casefold():
        return True
    if left.doi and right.doi and left.doi.casefold() == right.doi.casefold():
        return True
    if normalized_title_key(left.title) != normalized_title_key(right.title):
        return False
    left_authors = _author_keys(left)
    right_authors = _author_keys(right)
    return not left_authors or not right_authors or bool(left_authors & right_authors)


def _quality(event: ResearchEvent) -> tuple[float, int, int]:
    return (
        event.scores.source_reliability,
        len(event.abstract),
        int(bool(event.doi)) + int(bool(event.arxiv_id)),
    )


def _merge(preferred: ResearchEvent, other: ResearchEvent) -> ResearchEvent:
    preferred.provenance = sorted(
        {str(value): value for value in preferred.provenance + other.provenance}.values(),
        key=lambda value: (str(value.get("source_name")), str(value.get("primary_url"))),
    )
    preferred.other_urls = sorted(
        set(preferred.other_urls + other.other_urls + [other.primary_url]) - {preferred.primary_url}
    )
    preferred.categories = sorted(set(preferred.categories + other.categories))
    preferred.doi = preferred.doi or other.doi
    preferred.arxiv_id = preferred.arxiv_id or other.arxiv_id
    return preferred


def deduplicate_events(events: list[ResearchEvent]) -> list[ResearchEvent]:
    """Deduplicate the same work and same event; distinct event types remain distinct."""
    groups: list[list[ResearchEvent]] = []
    for event in sorted(events, key=lambda value: (value.published_at, value.event_id)):
        for group in groups:
            exemplar = group[0]
            if event.item_type == exemplar.item_type and _same_work(event, exemplar):
                group.append(event)
                break
        else:
            groups.append([event])

    result: list[ResearchEvent] = []
    for group in groups:
        preferred = max(group, key=_quality)
        for event in group:
            if event is not preferred:
                preferred = _merge(preferred, event)
        preferred.canonical_id = ResearchEvent.identity(
            title=preferred.title,
            authors=preferred.authors,
            arxiv_id=preferred.arxiv_id,
            doi=preferred.doi,
        )
        preferred.event_id = ResearchEvent.event_identity(
            preferred.canonical_id, preferred.item_type, preferred.published_at[:10]
        )
        result.append(preferred)
    return sorted(result, key=lambda event: (event.published_at, event.event_id), reverse=True)

