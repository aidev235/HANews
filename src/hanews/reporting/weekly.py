from __future__ import annotations

from datetime import datetime
from typing import Iterable

from hanews.models.item import Briefing, ResearchEvent, TranslatedBriefing
from hanews.models.run import ReportingWindow


def _label(value: str) -> str:
    return value.replace("[", "\\[").replace("]", "\\]").replace("\n", " ")


def _index(items: Iterable[ResearchEvent], *, translated: dict[str, TranslatedBriefing] | None = None) -> str:
    lines: list[str] = []
    for rank, event in enumerate(items, start=1):
        title = translated[event.event_id].title if translated else event.title
        lines.append(f"{rank}. [{_label(title)}]({event.primary_url})")
    return "\n".join(lines)


def _english_briefings(
    items: list[ResearchEvent], briefings: dict[str, Briefing]
) -> list[str]:
    sections: list[str] = []
    for rank, event in enumerate(
        [item for item in items if item.event_id in briefings], start=1
    ):
        briefing = briefings[event.event_id]
        topics = ", ".join(event.topics) or "Not specified"
        lines = [
            f"## {rank}. {event.title}",
            "",
            f"**Authors:** {', '.join(event.authors) or 'Not listed'}  ",
            f"**Source:** [{event.source_name}]({event.primary_url})  ",
            f"**Topics:** {topics}",
            "",
            "**Brief.**  ",
            briefing.brief,
            "",
            "**Why it matters.**  ",
            briefing.why_it_matters,
        ]
        if briefing.connections:
            lines.extend(["", "**Connections.**  ", briefing.connections])
        sections.append("\n".join(lines))
    return sections


def _chinese_briefings(
    items: list[ResearchEvent],
    briefings: dict[str, Briefing],
    translated: dict[str, TranslatedBriefing],
) -> list[str]:
    sections: list[str] = []
    for rank, event in enumerate(
        [item for item in items if item.event_id in briefings], start=1
    ):
        value = translated[event.event_id]
        topics = "、".join(value.topics) or "未注明"
        lines = [
            f"## {rank}. {value.title}",
            "",
            f"**作者：** {', '.join(event.authors) or '来源未列出'}  ",
            f"**来源：** [{event.source_name}]({event.primary_url})  ",
            f"**主题：** {topics}",
            "",
            "**简报。**  ",
            value.brief,
            "",
            "**重要性。**  ",
            value.why_it_matters,
        ]
        if value.connections:
            lines.extend(["", "**关联。**  ", value.connections])
        sections.append("\n".join(lines))
    return sections


def render_english_report(
    *,
    window: ReportingWindow,
    generated_at: datetime,
    timezone: str,
    model_label: str,
    ha_items: list[ResearchEvent],
    general_items: list[ResearchEvent],
    ha_briefings: dict[str, Briefing],
    general_briefings: dict[str, Briefing],
    configured_ha_count: int,
    configured_general_count: int,
) -> str:
    blocks = [
        "# HANews Weekly",
        f"## {window.start.isoformat()} — {window.end.isoformat()}",
        "",
        f"Generated: {generated_at.strftime('%Y-%m-%d %H:%M:%S %Z') or timezone}",
        f"Model: {model_label}",
        "",
        f"## Harmonic Analysis — Top {configured_ha_count}",
        "",
        _index(ha_items),
        "",
        f"## General Mathematics — Top {configured_general_count}",
        "",
        _index(general_items),
        "",
        "---",
        "",
        "# Harmonic Analysis Briefing",
        "",
        "\n\n".join(_english_briefings(ha_items, ha_briefings)),
        "",
        "# General Mathematics Briefing",
        "",
        "\n\n".join(_english_briefings(general_items, general_briefings)),
        "",
    ]
    return "\n".join(blocks).rstrip() + "\n"


def render_chinese_report(
    *,
    window: ReportingWindow,
    generated_at: datetime,
    timezone: str,
    model_label: str,
    ha_items: list[ResearchEvent],
    general_items: list[ResearchEvent],
    ha_briefings: dict[str, Briefing],
    general_briefings: dict[str, Briefing],
    translations: dict[str, TranslatedBriefing],
    configured_ha_count: int,
    configured_general_count: int,
) -> str:
    blocks = [
        "# HANews 周报",
        f"## {window.start.isoformat()} — {window.end.isoformat()}",
        "",
        f"生成时间：{generated_at.strftime('%Y-%m-%d %H:%M:%S %Z') or timezone}",
        f"模型：{model_label}",
        "",
        f"## 调和分析（Harmonic Analysis）— Top {configured_ha_count}",
        "",
        _index(ha_items, translated=translations),
        "",
        f"## 一般数学（General Mathematics）— Top {configured_general_count}",
        "",
        _index(general_items, translated=translations),
        "",
        "---",
        "",
        "# 调和分析简报",
        "",
        "\n\n".join(_chinese_briefings(ha_items, ha_briefings, translations)),
        "",
        "# 一般数学简报",
        "",
        "\n\n".join(_chinese_briefings(general_items, general_briefings, translations)),
        "",
    ]
    return "\n".join(blocks).rstrip() + "\n"
