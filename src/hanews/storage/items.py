from __future__ import annotations

import json
from pathlib import Path

from hanews.models.item import ResearchEvent


class ItemStore:
    """Append-only JSONL history with last-write-wins reads and idempotent appends."""

    def __init__(self, path: Path) -> None:
        self.path = path

    def load_latest(self) -> dict[str, ResearchEvent]:
        latest: dict[str, ResearchEvent] = {}
        if not self.path.exists():
            return latest
        with self.path.open("r", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                try:
                    event = ResearchEvent.from_dict(json.loads(line))
                except (TypeError, ValueError, json.JSONDecodeError) as exc:
                    raise ValueError(f"Corrupt JSONL at {self.path}:{line_number}: {exc}") from exc
                latest[event.event_id] = event
        return latest

    def append_changed(self, events: list[ResearchEvent]) -> int:
        latest = self.load_latest()
        additions: list[str] = []
        for event in sorted(events, key=lambda item: item.event_id):
            encoded = json.dumps(event.to_dict(), ensure_ascii=False, sort_keys=True)
            prior = latest.get(event.event_id)
            prior_encoded = (
                json.dumps(prior.to_dict(), ensure_ascii=False, sort_keys=True) if prior else None
            )
            if encoded != prior_encoded:
                additions.append(encoded)
        if not additions:
            return 0
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with self.path.open("a", encoding="utf-8", newline="\n") as handle:
            for encoded in additions:
                handle.write(encoded + "\n")
            handle.flush()
        return len(additions)

