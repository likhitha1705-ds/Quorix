"""Development ticket adapter (structured JSON)."""
from __future__ import annotations

from pathlib import Path

from pydantic import ValidationError

from app.core.text import normalize_text
from app.ingestion.authority import SOURCE_DEFAULTS, resolve_authority
from app.ingestion.base import RecordValidationError, SourceAdapter, read_json_objects
from app.schemas.source import (
    KnowledgeSource,
    SourceRecord,
    SourceType,
    TextSegment,
    TicketInput,
)


class TicketAdapter(SourceAdapter):
    source_type = SourceType.TICKET
    default_source_id = "src_tickets"

    def source_definition(self) -> KnowledgeSource:
        return KnowledgeSource(
            source_id=self.source_id,
            source_type=self.source_type,
            name="Development Tickets",
            description="Bug reports, feature requests, implementation tasks and resolutions.",
            authority_level=SOURCE_DEFAULTS[self.source_type],
            authority_basis="depends on ticket status",
        )

    def discover(self) -> list[Path]:
        return sorted((self.data_dir / "tickets").glob("*.json"))

    def parse(self, path: Path) -> list[SourceRecord]:
        records = []
        for raw in read_json_objects(path):
            try:
                t = TicketInput.model_validate(raw)
            except ValidationError as exc:
                raise RecordValidationError(str(exc)) from exc
            records.append(self._normalize(t, path))
        return records

    def _normalize(self, t: TicketInput, path: Path) -> SourceRecord:
        head = [f"Ticket {t.ticket_id}: {t.title}", f"Status: {t.status}"]
        if t.priority:
            head.append(f"Priority: {t.priority}")
        if t.assignee:
            head.append(f"Assignee: {t.assignee}")
        if t.labels:
            head.append("Labels: " + ", ".join(t.labels))
        head.append(f"Created: {t.created_at:%Y-%m-%d} | Updated: {t.updated_at:%Y-%m-%d}")
        segments = [
            TextSegment(
                text="\n".join(head) + "\n\nDescription:\n" + normalize_text(t.description),
                label="description",
                timestamp=t.created_at,
            )
        ]
        for i, c in enumerate(sorted(t.comments, key=lambda c: c.timestamp), start=1):
            segments.append(
                TextSegment(
                    text=f"Comment by {c.author} [{c.timestamp:%Y-%m-%d}]: {normalize_text(c.content)}",
                    label=f"comment-{i}",
                    speaker=c.author,
                    timestamp=c.timestamp,
                )
            )
        if t.resolution:
            segments.append(
                TextSegment(
                    text="Resolution: " + normalize_text(t.resolution),
                    label="resolution",
                    timestamp=t.resolved_at or t.updated_at,
                )
            )
        metadata = {
            **t.metadata,
            "ticket_id": t.ticket_id,
            "priority": t.priority,
            "assignee": t.assignee,
            "reporter": t.reporter,
            "labels": t.labels,
            "resolution": t.resolution,
            "resolved_at": t.resolved_at.isoformat() if t.resolved_at else None,
            "comment_count": len(t.comments),
        }
        level, basis = resolve_authority(self.source_type, t.status, metadata, t.authority_level)
        return SourceRecord(
            source_id=self.source_id,
            source_type=self.source_type,
            original_record_id=t.ticket_id,
            title=t.title,
            content="\n\n".join(s.text for s in segments),
            description=None,
            source_reference=f"{self.relative_reference(path)}#{t.ticket_id}",
            author=t.reporter or t.assignee,
            status=t.status,
            created_at=t.created_at,
            updated_at=t.updated_at,
            authority_level=level,
            authority_basis=basis,
            metadata=metadata,
            segments=segments,
        )
