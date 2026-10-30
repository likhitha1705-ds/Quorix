"""Semantic retrieval engine using Qdrant vector search."""
from __future__ import annotations

import logging
import time
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.http import models as qm

from app.retrieval.adapters import (
    ConversationRetrievalAdapter,
    DocumentRetrievalAdapter,
    RetrievalAdapterRegistry,
    TicketRetrievalAdapter,
)
from app.schemas.intelligence import RankedSource
from app.schemas.retrieval import RetrievedChunk

log = logging.getLogger(__name__)


class SemanticRetrievalEngine:
    """Performs semantic vector search across selected sources using Qdrant."""

    def __init__(
        self,
        client: QdrantClient | None = None,
        embedder: Any = None,
        collection: str = "quorix_chunks",
        adapter_registry: RetrievalAdapterRegistry | None = None,
    ) -> None:
        self.client = client
        self.embedder = embedder
        self.collection = collection
        self.adapter_registry = adapter_registry or RetrievalAdapterRegistry(
            [
                DocumentRetrievalAdapter(client=client, collection=collection),
                ConversationRetrievalAdapter(client=client, collection=collection),
                TicketRetrievalAdapter(client=client, collection=collection),
            ]
        )

    def search(
        self,
        query: str,
        selected_sources: list[RankedSource],
        limit_per_source: dict[str, int] | None = None,
        total_limit: int = 10,
    ) -> tuple[list[RetrievedChunk], float]:
        """Execute semantic search only on sources selected by Phase 3.

        Returns (retrieved_chunks, latency_ms).
        """
        start_time = time.perf_counter()
        if not selected_sources or not query.strip():
            return [], 0.0

        query_vector = self._embed_query(query)
        if query_vector is None:
            log.warning("Embedding service returned None for query; semantic search skipped")
            return [], round((time.perf_counter() - start_time) * 1000, 2)

        retrieved_chunks: list[RetrievedChunk] = []

        # Query each selected source via its corresponding adapter
        for src in selected_sources:
            adapter = self.adapter_registry.get_adapter(src.source_type)
            chunk_limit = (limit_per_source or {}).get(src.source_id, total_limit)

            if adapter is not None:
                chunks = adapter.retrieve(
                    query=query,
                    query_vector=query_vector,
                    source_id=src.source_id,
                    limit=chunk_limit,
                    source_name=src.source_name,
                )
                retrieved_chunks.extend(chunks)
            else:
                log.warning("No retrieval adapter found for source type %s", src.source_type)

        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
        log.debug("Semantic retrieval found %d chunks in %.2fms", len(retrieved_chunks), latency_ms)
        return retrieved_chunks, latency_ms

    def _embed_query(self, query: str) -> list[float] | None:
        """Embed the query string into a vector using the configured embedder."""
        if self.embedder is None:
            return None

        try:
            if hasattr(self.embedder, "embed_query"):
                return self.embedder.embed_query(query)
            if hasattr(self.embedder, "embed_documents"):
                vectors = self.embedder.embed_documents([query])
                return vectors[0] if vectors else None
        except Exception as exc:
            log.warning("Error embedding query %r: %s", query, exc)
            return None

        return None

