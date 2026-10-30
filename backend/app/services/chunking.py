"""Reusable chunking service: packs whole segments (messages, comments, sections)
into chunks and only splits a segment that exceeds the chunk size."""
from __future__ import annotations

from app.core.ids import chunk_point_id, make_chunk_id
from app.core.text import normalize_text
from app.schemas.source import Chunk, SourceRecord, TextSegment


class ChunkingService:
    def __init__(self, chunk_size: int = 900, chunk_overlap: int = 120) -> None:
        if chunk_size < 50:
            raise ValueError("chunk_size must be >= 50")
        if not 0 <= chunk_overlap < chunk_size // 2:
            raise ValueError("chunk_overlap must be >= 0 and < chunk_size / 2")
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    # -- splitting ---------------------------------------------------------
    def _split_long(self, seg: TextSegment) -> list[TextSegment]:
        text = seg.text
        if len(text) <= self.chunk_size:
            return [seg]
        # Keep the speaker prefix on every piece of a long message.
        prefix = ""
        if seg.speaker and text.startswith(seg.speaker):
            head, sep, _ = text.partition(": ")
            if sep:
                prefix = head + ": "
        budget = self.chunk_size - len(prefix)
        pieces, start = [], len(prefix)
        while start < len(text):
            end = min(start + budget, len(text))
            if end < len(text):  # prefer a whitespace boundary in the last 25%
                cut = text.rfind(" ", start + int(budget * 0.75), end)
                end = cut if cut > start else end
            piece = text[start:end].strip()
            if piece:
                pieces.append(seg.model_copy(update={"text": prefix + piece}))
            if end >= len(text):
                break
            start = max(end - self.chunk_overlap, start + 1)
        return pieces

    def _pack(self, segments: list[TextSegment]) -> list[list[TextSegment]]:
        groups: list[list[TextSegment]] = []
        cur: list[TextSegment] = []
        cur_len = 0
        for seg in (p for s in segments for p in self._split_long(s)):
            added = len(seg.text) + (2 if cur else 0)
            if cur and cur_len + added > self.chunk_size:
                groups.append(cur)
                # carry trailing segments (<= overlap chars) for conversational context
                carry, carry_len = [], 0
                for prev in reversed(cur):
                    if carry_len + len(prev.text) > self.chunk_overlap:
                        break
                    carry.insert(0, prev)
                    carry_len += len(prev.text) + 2
                cur, cur_len = carry, carry_len
                added = len(seg.text) + (2 if cur else 0)
            cur.append(seg)
            cur_len += added
        if cur and (not groups or any(s not in groups[-1] for s in cur)):
            groups.append(cur)
        return groups

    # -- public API ----------------------------------------------------------
    def chunk_record(self, record: SourceRecord) -> list[Chunk]:
        segments = record.segments or [
            TextSegment(text=p) for p in normalize_text(record.content).split("\n\n") if p.strip()
        ]
        chunks: list[Chunk] = []
        for group in self._pack(segments):
            text = "\n\n".join(s.text for s in group).strip()
            if not text:
                continue
            idx = len(chunks)
            chunk_id = make_chunk_id(record.document_id, idx)
            times = [s.timestamp for s in group if s.timestamp]
            chunks.append(
                Chunk(
                    chunk_id=chunk_id,
                    point_id=chunk_point_id(chunk_id),
                    document_id=record.document_id,
                    source_id=record.source_id,
                    source_type=record.source_type,
                    original_record_id=record.original_record_id,
                    chunk_index=idx,
                    text=text,
                    title=record.title,
                    source_reference=record.source_reference,
                    status=record.status,
                    author=record.author,
                    created_at=record.created_at,
                    updated_at=record.updated_at,
                    authority_level=record.authority_level,
                    authority_basis=record.authority_basis,
                    segment_labels=list(dict.fromkeys(s.label for s in group if s.label)),
                    speakers=list(dict.fromkeys(s.speaker for s in group if s.speaker)),
                    time_start=min(times) if times else None,
                    time_end=max(times) if times else None,
                )
            )
        return chunks
