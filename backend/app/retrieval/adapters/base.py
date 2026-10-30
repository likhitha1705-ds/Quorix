"""Base interface for source retrieval adapters."""
from __future__ import annotations

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any

from app.schemas.retrieval import RetrievedChunk


class BaseRetrievalAdapter(ABC):
    """Common interface hiding internal storage implementations from the retrieval engine."""

    source_type: str

    @abstractmethod
    def retrieve(
        self,
        query: str,
        query_vector: list[float] | None,
        source_id: str,
        limit: int,
        source_name: str | None = None,
    ) -> list[RetrievedChunk]:
        """Retrieve and return normalized chunks for the given source and query."""
        raise NotImplementedError

    def normalize_chunk_payload(
        self,
        payload: dict[str, Any],
        score: float = 0.0,
        default_source_name: str | None = None,
    ) -> RetrievedChunk:
        """Convert a raw storage payload (from Qdrant or DB) into a normalized RetrievedChunk."""
        chunk_id = payload.get("chunk_id") or "unknown_chunk"
        source_id = payload.get("source_id") or "unknown_source"
        source_type = payload.get("source_type") or self.source_type
        source_name = default_source_name or payload.get("source_name") or payload.get("title") or source_id
        content = payload.get("text") or payload.get("content") or ""

        # Parse timestamp if present
        raw_ts = payload.get("updated_at") or payload.get("created_at")
        ts: datetime | None = None
        if isinstance(raw_ts, str):
            try:
                ts = datetime.fromisoformat(raw_ts)
            except Exception:
                ts = None
        elif isinstance(raw_ts, datetime):
            ts = raw_ts

        # Metadata dictionary
        metadata = {
            "document_id": payload.get("document_id"),
            "original_record_id": payload.get("original_record_id"),
            "title": payload.get("title"),
            "source_reference": payload.get("source_reference"),
            "status": payload.get("status"),
            "author": payload.get("author"),
            "authority_level": payload.get("authority_level", 0.5),
            "authority_basis": payload.get("authority_basis"),
            "speakers": payload.get("speakers", []),
            "segment_labels": payload.get("segment_labels", []),
        }

        return RetrievedChunk(
            chunk_id=chunk_id,
            source_id=source_id,
            source_type=source_type,
            source_name=source_name,
            content=content,
            similarity_score=score,
            keyword_score=0.0,
            final_score=score,
            timestamp=ts,
            metadata=metadata,
        )

