"""Engineering conversation adapter (structured JSON)."""
from __future__ import annotations

from pathlib import Path

from pydantic import ValidationError

from app.core.text import normalize_text
from app.ingestion.authority import SOURCE_DEFAULTS, resolve_authority
from app.ingestion.base import RecordValidationError, SourceAdapter, read_json_objects
from app.schemas.source import (
    ConversationInput,
    KnowledgeSource,
    SourceRecord,
    SourceType,
    TextSegment,
)


class ConversationAdapter(SourceAdapter):
    source_type = SourceType.CONVERSATION
    default_source_id = "src_conversations"

    def source_definition(self) -> KnowledgeSource:
        return KnowledgeSource(
            source_id=self.source_id,
            source_type=self.source_type,
            name="Engineering Conversations",
            description="Engineering discussions, design decisions and debugging threads.",
            authority_level=SOURCE_DEFAULTS[self.source_type],
            authority_basis="informal discussion unless marked as a decision",
        )

    def discover(self) -> list[Path]:
        return sorted((self.data_dir / "conversations").glob("*.json"))

    def parse(self, path: Path) -> list[SourceRecord]:
        records = []
        for raw in read_json_objects(path):
            try:
                conv = ConversationInput.model_validate(raw)
            except ValidationError as exc:
                raise RecordValidationError(str(exc)) from exc
            records.append(self._normalize(conv, path))
        return records

    def _normalize(self, conv: ConversationInput, path: Path) -> SourceRecord:
        msgs = sorted(conv.messages, key=lambda m: m.timestamp)  # stable: keeps ties in order
        segments, lines, ids = [], [], set()
        for i, m in enumerate(msgs, start=1):
            mid = m.message_id or f"m{i}"
            if mid in ids:
                raise RecordValidationError(f"duplicate message_id {mid!r}")
            ids.add(mid)
            ts = m.timestamp.strftime("%Y-%m-%d %H:%M UTC")
            line = f"{m.speaker} [{ts}]: {normalize_text(m.content)}"
            lines.append(line)
            segments.append(
                TextSegment(text=line, label=mid, speaker=m.speaker, timestamp=m.timestamp)
            )
        participants = sorted(set(conv.participants) | {m.speaker for m in msgs})
        metadata = {
            **conv.metadata,
            "conversation_id": conv.conversation_id,
            "participants": participants,
            "message_count": len(msgs),
            "message_ids": [s.label for s in segments],
            "channel": conv.channel,
        }
        level, basis = resolve_authority(
            self.source_type, conv.status, metadata, conv.authority_level
        )
        return SourceRecord(
            source_id=self.source_id,
            source_type=self.source_type,
            original_record_id=conv.conversation_id,
            title=conv.title,
            content="\n".join(lines),
            description=conv.description,
            source_reference=f"{self.relative_reference(path)}#{conv.conversation_id}",
            author=msgs[0].speaker,
            status=conv.status,
            created_at=conv.created_at or msgs[0].timestamp,
            updated_at=conv.updated_at or msgs[-1].timestamp,
            authority_level=level,
            authority_basis=basis,
            metadata=metadata,
            segments=segments,
        )
