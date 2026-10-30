"""Deduplication module: eliminates duplicate chunks across sources and retrieval strategies."""
from __future__ import annotations

import hashlib
import logging

from app.schemas.retrieval import RetrievedChunk

log = logging.getLogger(__name__)


class ChunkDeduplicator:
    """Removes duplicate chunks, keeping the highest-ranked version and preserving source metadata."""

    def deduplicate(self, chunks: list[RetrievedChunk]) -> list[RetrievedChunk]:
        """Deduplicate chunks by chunk_id and content hash. Assumes chunks are sorted by score descending."""
        seen_ids: set[str] = set()
        seen_hashes: dict[str, RetrievedChunk] = {}
        deduped: list[RetrievedChunk] = []

        for chunk in chunks:
            # 1. Exact chunk_id deduplication
            if chunk.chunk_id in seen_ids:
                log.debug("Skipping duplicate chunk_id: %s", chunk.chunk_id)
                continue

            # 2. Content hash deduplication
            content_key = self._hash_content(chunk.content)
            if content_key in seen_hashes:
                existing_chunk = seen_hashes[content_key]
                # Maintain metadata on the kept version
                alt_refs = existing_chunk.metadata.setdefault("alternate_references", [])
                alt_refs.append(
                    {
                        "chunk_id": chunk.chunk_id,
                        "source_id": chunk.source_id,
                        "source_name": chunk.source_name,
                        "source_reference": chunk.metadata.get("source_reference"),
                    }
                )
                log.debug(
                    "Duplicate content detected for chunk %s (kept higher-ranked %s)",
                    chunk.chunk_id,
                    existing_chunk.chunk_id,
                )
                continue

            seen_ids.add(chunk.chunk_id)
            seen_hashes[content_key] = chunk
            deduped.append(chunk)

        log.debug("Deduplicated %d raw chunks down to %d unique chunks", len(chunks), len(deduped))
        return deduped

    @staticmethod
    def _hash_content(content: str) -> str:
        """Normalized hash of chunk content to detect identical text."""
        normalized = " ".join(content.strip().lower().split())
        return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

