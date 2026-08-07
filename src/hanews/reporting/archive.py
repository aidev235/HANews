from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from pathlib import Path

from hanews.models.run import ReportingWindow
from hanews.storage.atomic import atomic_write_text


@dataclass
class ArchiveWriteResult:
    path: Path
    status: str
    revisions_created: list[Path] = field(default_factory=list)


class ArchiveManager:
    def __init__(self, root: Path, directory: str, preserve_revisions: bool = True) -> None:
        self.root = root
        self.archive_dir = root / directory
        self.preserve_revisions = preserve_revisions

    @staticmethod
    def _hash(content: str) -> str:
        return hashlib.sha256(content.encode("utf-8")).hexdigest()[:16]

    def _write(self, path: Path, content: str, revision_group: str) -> ArchiveWriteResult:
        if not path.exists():
            atomic_write_text(path, content)
            return ArchiveWriteResult(path=path, status="created")
        existing = path.read_text(encoding="utf-8")
        if existing == content:
            return ArchiveWriteResult(path=path, status="unchanged")
        revisions: list[Path] = []
        if self.preserve_revisions:
            revision = (
                self.archive_dir
                / "revisions"
                / revision_group
                / f"{path.stem}-{self._hash(existing)}{path.suffix}"
            )
            if not revision.exists():
                atomic_write_text(revision, existing)
                revisions.append(revision)
        atomic_write_text(path, content)
        return ArchiveWriteResult(path=path, status="updated", revisions_created=revisions)

    def write_week(
        self, window: ReportingWindow, english: str, chinese: str
    ) -> tuple[ArchiveWriteResult, ArchiveWriteResult]:
        stem = window.archive_stem
        english_path = self.archive_dir / f"{stem}.md"
        chinese_path = self.archive_dir / f"{stem}-zh.md"
        return (
            self._write(english_path, english, stem),
            self._write(chinese_path, chinese, stem),
        )

