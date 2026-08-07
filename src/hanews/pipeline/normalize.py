from __future__ import annotations

import re
from datetime import date
from urllib.parse import urlparse

from hanews.models.item import ResearchEvent
from hanews.models.run import ReportingWindow


def normalize_whitespace(value: str) -> str:
    return " ".join(value.split())


def normalize_doi(value: str | None) -> str | None:
    if not value:
        return None
    normalized = value.strip().casefold()
    normalized = re.sub(r"^https?://(?:dx\.)?doi\.org/", "", normalized)
    normalized = re.sub(r"^doi:\s*", "", normalized)
    return normalized or None


def valid_http_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _timeliness(event_date: date, window: ReportingWindow) -> float:
    distance = max(0, (window.end - event_date).days)
    return max(0.0, min(1.0, 1.0 - 0.04 * distance))


def normalize_event(event: ResearchEvent, window: ReportingWindow) -> ResearchEvent:
    event.title = normalize_whitespace(event.title)
    event.authors = [normalize_whitespace(name) for name in event.authors if name.strip()]
    event.abstract = normalize_whitespace(event.abstract)
    event.doi = normalize_doi(event.doi)
    event.categories = sorted(set(value.strip() for value in event.categories if value.strip()))
    event.other_urls = sorted(set(url for url in event.other_urls if valid_http_url(url)))
    if not event.title:
        raise ValueError(f"Event {event.event_id} has an empty title")
    if not valid_http_url(event.primary_url):
        raise ValueError(f"Event {event.event_id} has invalid primary URL: {event.primary_url}")
    try:
        published = date.fromisoformat(event.published_at[:10])
    except ValueError as exc:
        raise ValueError(f"Event {event.event_id} has invalid publication date") from exc
    event.scores.timeliness = _timeliness(published, window)
    event.canonical_id = ResearchEvent.identity(
        title=event.title, authors=event.authors, arxiv_id=event.arxiv_id, doi=event.doi
    )
    event.event_id = ResearchEvent.event_identity(
        event.canonical_id, event.item_type, event.published_at[:10]
    )
    return event


def normalize_events(events: list[ResearchEvent], window: ReportingWindow) -> list[ResearchEvent]:
    normalized: list[ResearchEvent] = []
    for event in events:
        normalized.append(normalize_event(event, window))
    return normalized

