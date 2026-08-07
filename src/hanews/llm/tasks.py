from __future__ import annotations

from pathlib import Path
from typing import Any

from hanews.config import ModelConfig
from hanews.llm.client import LLMClient, LLMResponse
from hanews.models.item import Briefing, ResearchEvent, TranslatedBriefing


def _read_prompt(root: Path, name: str) -> str:
    return (root / "prompts" / name).read_text(encoding="utf-8")


def _object(properties: dict[str, Any], required: list[str] | None = None) -> dict[str, Any]:
    return {
        "type": "object",
        "properties": properties,
        "required": required or list(properties),
        "additionalProperties": False,
    }


CLASSIFICATION_ITEM_SCHEMA = _object(
    {
        "event_id": {"type": "string"},
        "coverage": {
            "type": "string",
            "enum": ["harmonic_analysis", "general_mathematics", "exclude"],
        },
        "ha_relationship": {
            "type": "string",
            "enum": ["direct", "strongly_adjacent", "superficial", "unrelated"],
        },
        "topics": {"type": "array", "items": {"type": "string"}},
        "harmonic_analysis_relevance": {"type": "number"},
        "mathematical_importance": {"type": "number"},
        "novelty": {"type": "number"},
        "research_interest": {"type": "number"},
        "confidence": {"type": "number"},
        "rationale": {"type": "string"},
    }
)

CLASSIFICATION_SCHEMA = _object(
    {"assessments": {"type": "array", "items": CLASSIFICATION_ITEM_SCHEMA}}
)

BRIEFING_ITEM_SCHEMA = _object(
    {
        "event_id": {"type": "string"},
        "brief": {"type": "string"},
        "why_it_matters": {"type": "string"},
        "connections": {"type": "string"},
    }
)

BRIEFING_SCHEMA = _object({"briefings": {"type": "array", "items": BRIEFING_ITEM_SCHEMA}})

TRANSLATION_ITEM_SCHEMA = _object(
    {
        "event_id": {"type": "string"},
        "title": {"type": "string"},
        "topics": {"type": "array", "items": {"type": "string"}},
        "brief": {"type": "string"},
        "why_it_matters": {"type": "string"},
        "connections": {"type": "string"},
    }
)

TRANSLATION_SCHEMA = _object(
    {"translations": {"type": "array", "items": TRANSLATION_ITEM_SCHEMA}}
)


def _event_metadata(event: ResearchEvent) -> dict[str, Any]:
    return {
        "event_id": event.event_id,
        "title": event.title,
        "authors": event.authors,
        "abstract_or_description": event.abstract,
        "item_type": event.item_type,
        "source_name": event.source_name,
        "primary_url": event.primary_url,
        "published_at": event.published_at,
        "updated_at": event.updated_at,
        "doi": event.doi,
        "arxiv_id": event.arxiv_id,
        "categories": event.categories,
    }


def _require_exact_ids(expected: set[str], received: list[dict[str, Any]], label: str) -> None:
    actual = [str(item.get("event_id", "")) for item in received]
    if len(actual) != len(set(actual)):
        raise ValueError(f"{label} response contains duplicate event_id values")
    if set(actual) != expected:
        raise ValueError(
            f"{label} response IDs differ from request: missing={sorted(expected - set(actual))}, "
            f"extra={sorted(set(actual) - expected)}"
        )


def classify_events(
    client: LLMClient,
    model: ModelConfig,
    events: list[ResearchEvent],
    *,
    root: Path,
    topics: dict[str, Any],
    batch_size: int = 12,
) -> list[LLMResponse]:
    responses: list[LLMResponse] = []
    prompt = _read_prompt(root, "relevance.md") + "\n\nTopic policy:\n" + str(topics)
    for offset in range(0, len(events), batch_size):
        batch = events[offset : offset + batch_size]
        response = client.generate_json(
            task="classify_research_events",
            model=model,
            instructions=prompt,
            payload={"items": [_event_metadata(event) for event in batch]},
            schema=CLASSIFICATION_SCHEMA,
        )
        assessments = response.data.get("assessments")
        if not isinstance(assessments, list):
            raise ValueError("Classification response is missing assessments")
        _require_exact_ids({event.event_id for event in batch}, assessments, "classification")
        by_id = {event.event_id: event for event in batch}
        for assessment in assessments:
            event = by_id[str(assessment["event_id"])]
            event.coverage = str(assessment["coverage"])
            event.ha_relationship = str(assessment["ha_relationship"])
            event.topics = [str(value) for value in assessment["topics"]]
            event.scores.harmonic_analysis_relevance = float(
                assessment["harmonic_analysis_relevance"]
            )
            event.scores.mathematical_importance = float(assessment["mathematical_importance"])
            event.scores.novelty = float(assessment["novelty"])
            event.scores.research_interest = float(assessment["research_interest"])
            event.scores.confidence = float(assessment["confidence"])
            event.scores.validate()
            event.assessment_rationale = str(assessment["rationale"])
        responses.append(response)
    return responses


def summarize_events(
    client: LLMClient,
    model: ModelConfig,
    events: list[ResearchEvent],
    *,
    root: Path,
) -> tuple[dict[str, Briefing], LLMResponse | None]:
    if not events:
        return {}, None
    response = client.generate_json(
        task="write_research_briefings",
        model=model,
        instructions=_read_prompt(root, "item-summary.md"),
        payload={"items": [_event_metadata(event) for event in events]},
        schema=BRIEFING_SCHEMA,
    )
    values = response.data.get("briefings")
    if not isinstance(values, list):
        raise ValueError("Briefing response is missing briefings")
    _require_exact_ids({event.event_id for event in events}, values, "briefing")
    briefings = {
        str(value["event_id"]): Briefing(
            event_id=str(value["event_id"]),
            brief=str(value["brief"]),
            why_it_matters=str(value["why_it_matters"]),
            connections=str(value["connections"]),
        )
        for value in values
    }
    return briefings, response


def translate_briefings(
    client: LLMClient,
    model: ModelConfig,
    events: list[ResearchEvent],
    briefings: dict[str, Briefing],
    *,
    root: Path,
) -> tuple[dict[str, TranslatedBriefing], LLMResponse | None]:
    if not events:
        return {}, None
    translation_payload = []
    for event in events:
        briefing = briefings.get(event.event_id)
        translation_payload.append(
            {
                "event_id": event.event_id,
                "title": event.title,
                "topics": event.topics,
                "brief": briefing.brief if briefing else "",
                "why_it_matters": briefing.why_it_matters if briefing else "",
                "connections": briefing.connections if briefing else "",
            }
        )
    response = client.generate_json(
        task="translate_finalized_report_fields_zh",
        model=model,
        instructions=_read_prompt(root, "translation-zh.md"),
        payload={"finalized_english_fields": translation_payload},
        schema=TRANSLATION_SCHEMA,
    )
    values = response.data.get("translations")
    if not isinstance(values, list):
        raise ValueError("Translation response is missing translations")
    _require_exact_ids({event.event_id for event in events}, values, "translation")
    translations = {
        str(value["event_id"]): TranslatedBriefing(
            event_id=str(value["event_id"]),
            title=str(value["title"]),
            topics=[str(topic) for topic in value["topics"]],
            brief=str(value["brief"]),
            why_it_matters=str(value["why_it_matters"]),
            connections=str(value["connections"]),
        )
        for value in values
    }
    return translations, response
