from __future__ import annotations

import re
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from typing import Any

from hanews.collectors.base import Collector, CollectorResult
from hanews.models.item import ResearchEvent
from hanews.models.run import ReportingWindow


ATOM = "{http://www.w3.org/2005/Atom}"
ARXIV = "{http://arxiv.org/schemas/atom}"


def _text(element: ET.Element | None) -> str:
    return "" if element is None or element.text is None else " ".join(element.text.split())


def _arxiv_id(raw_id: str) -> str:
    value = raw_id.rsplit("/", 1)[-1]
    return re.sub(r"v\d+$", "", value)


class ArxivCollector(Collector):
    name = "arxiv"

    def __init__(self, source: dict[str, Any], network: dict[str, Any]) -> None:
        self.base_url = str(source["base_url"])
        self.categories = [str(value) for value in source.get("categories", [])]
        self.max_results = int(source.get("max_results", 300))
        self.reliability = float(source.get("reliability", 0.95))
        self.timeout = float(network.get("timeout_seconds", 30))
        self.max_attempts = int(network.get("max_attempts", 3))
        self.user_agent = str(network.get("user_agent", "HANews/0.1"))

    def _url(self, window: ReportingWindow) -> str:
        category_query = " OR ".join(f"cat:{category}" for category in self.categories)
        start = window.start.strftime("%Y%m%d0000")
        end = window.end.strftime("%Y%m%d2359")
        query = f"({category_query}) AND submittedDate:[{start} TO {end}]"
        params = urllib.parse.urlencode(
            {
                "search_query": query,
                "start": 0,
                "max_results": self.max_results,
                "sortBy": "submittedDate",
                "sortOrder": "descending",
            }
        )
        return f"{self.base_url}?{params}"

    def _retrieve(self, url: str) -> bytes:
        request = urllib.request.Request(url, headers={"User-Agent": self.user_agent})
        last_error: Exception | None = None
        for attempt in range(1, self.max_attempts + 1):
            try:
                with urllib.request.urlopen(request, timeout=self.timeout) as response:
                    return response.read()
            except Exception as exc:  # network exceptions vary by Python/platform
                last_error = exc
                if attempt < self.max_attempts:
                    time.sleep(min(2 ** (attempt - 1), 4))
        assert last_error is not None
        raise last_error

    def _parse(self, body: bytes, retrieved_at: str) -> list[ResearchEvent]:
        root = ET.fromstring(body)
        events: list[ResearchEvent] = []
        for entry in root.findall(f"{ATOM}entry"):
            raw_id = _text(entry.find(f"{ATOM}id"))
            identifier = _arxiv_id(raw_id)
            title = _text(entry.find(f"{ATOM}title"))
            authors = [
                _text(author.find(f"{ATOM}name"))
                for author in entry.findall(f"{ATOM}author")
            ]
            abstract = _text(entry.find(f"{ATOM}summary"))
            published = _text(entry.find(f"{ATOM}published"))
            updated = _text(entry.find(f"{ATOM}updated")) or None
            doi = _text(entry.find(f"{ARXIV}doi")) or None
            categories = [
                value
                for category in entry.findall(f"{ATOM}category")
                if (value := category.attrib.get("term"))
            ]
            primary_url = f"https://arxiv.org/abs/{identifier}"
            canonical_id = ResearchEvent.identity(
                title=title, authors=authors, arxiv_id=identifier, doi=doi
            )
            event_date = published[:10]
            item_type = "NEW_PREPRINT"
            event_id = ResearchEvent.event_identity(canonical_id, item_type, event_date)
            events.append(
                ResearchEvent(
                    canonical_id=canonical_id,
                    event_id=event_id,
                    title=title,
                    authors=authors,
                    abstract=abstract,
                    item_type=item_type,
                    source_name=self.name,
                    primary_url=primary_url,
                    discovery_url=self._url_placeholder(),
                    published_at=published,
                    updated_at=updated,
                    discovered_at=retrieved_at,
                    doi=doi,
                    arxiv_id=identifier,
                    categories=categories,
                    other_urls=[raw_id] if raw_id and raw_id != primary_url else [],
                    provenance=[
                        {
                            "source_name": self.name,
                            "primary_url": primary_url,
                            "retrieved_at": retrieved_at,
                        }
                    ],
                )
            )
        return events

    def _url_placeholder(self) -> str:
        # The exact query URL is filled by collect, keeping parsing independently testable.
        return self.base_url

    def collect(self, window: ReportingWindow, retrieved_at: str) -> CollectorResult:
        url = self._url(window)
        try:
            events = self._parse(self._retrieve(url), retrieved_at)
            for event in events:
                event.discovery_url = url
                event.scores.source_reliability = self.reliability
            return CollectorResult(
                source_name=self.name,
                status="success",
                events=events,
                metadata={"query_url": url, "retrieved_at": retrieved_at},
            )
        except Exception as exc:
            return CollectorResult(
                source_name=self.name,
                status="failed",
                errors=[f"{type(exc).__name__}: {exc}"],
                metadata={"query_url": url, "retrieved_at": retrieved_at},
            )


def build_collectors(sources: list[dict[str, Any]], network: dict[str, Any]) -> list[Collector]:
    collectors: list[Collector] = []
    for source in sources:
        if not source.get("enabled", True):
            continue
        kind = source.get("collector")
        if kind == "arxiv":
            collectors.append(ArxivCollector(source, network))
        else:
            raise ValueError(f"Unknown collector type: {kind}")
    return collectors
