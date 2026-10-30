"""Common ingestion interface. Future connectors (GitHub, Slack, Notion, Jira)
implement SourceAdapter: describe the source, discover raw items, parse each into
normalized SourceRecords."""
from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, ClassVar, Iterator

from app.schemas.source import KnowledgeSource, SourceRecord, SourceType

log = logging.getLogger(__name__)


class RecordValidationError(ValueError):
    """Raised when an original record is invalid and cannot be ingested."""


@dataclass
class LoadResult:
    reference: str
    records: list[SourceRecord]
    error: str | None = None


class SourceAdapter(ABC):
    source_type: ClassVar[SourceType]
    default_source_id: ClassVar[str]

    def __init__(self, data_dir: Path, source_id: str | None = None) -> None:
        self.data_dir = Path(data_dir)
        self.source_id = source_id or self.default_source_id

    @abstractmethod
    def source_definition(self) -> KnowledgeSource:
        """Registry entry for this source."""

    @abstractmethod
    def discover(self) -> list[Path]:
        """Raw items (files) belonging to this source."""

    @abstractmethod
    def parse(self, path: Path) -> list[SourceRecord]:
        """Parse one raw item into normalized records. Raise RecordValidationError."""

    def relative_reference(self, path: Path) -> str:
        try:
            return path.resolve().relative_to(self.data_dir.resolve()).as_posix()
        except ValueError:
            return path.name

    def iter_records(self) -> Iterator[LoadResult]:
        """Yield one LoadResult per raw item; parse errors never abort the run."""
        for path in self.discover():
            ref = self.relative_reference(path)
            try:
                yield LoadResult(ref, self.parse(path))
            except Exception as exc:  # noqa: BLE001 - reported, not swallowed
                log.warning("Failed to parse %s: %s", ref, exc)
                yield LoadResult(ref, [], error=f"{type(exc).__name__}: {exc}")


def read_json_objects(path: Path) -> list[dict[str, Any]]:
    """A JSON file may hold one object or a list of objects."""
    try:
        data = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RecordValidationError(f"cannot read JSON: {exc}") from exc
    items = data if isinstance(data, list) else [data]
    if not items or not all(isinstance(i, dict) for i in items):
        raise RecordValidationError("JSON must be an object or a non-empty list of objects")
    return items
