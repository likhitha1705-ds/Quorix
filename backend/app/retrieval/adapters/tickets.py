"""Retrieval adapter for development tickets."""
from __future__ import annotations

import logging

from qdrant_client import QdrantClient
from qdrant_client.http import models as qm

from app.retrieval.adapters.base import BaseRetrievalAdapter
from app.schemas.retrieval import RetrievedChunk

log = logging.getLogger(__name__)


class TicketRetrievalAdapter(BaseRetrievalAdapter):
    """Adapter for retrieving chunks from issue tickets, bug reports, and tasks."""

    source_type = "ticket"

    def __init__(self, client: QdrantClient | None = None, collection: str = "quorix_chunks") -> None:
        self.client = client
        self.collection = collection

    def retrieve(
        self,
        query: str,
        query_vector: list[float] | None,
        source_id: str,
        limit: int,
        source_name: str | None = None,
    ) -> list[RetrievedChunk]:
        """Query Qdrant for ticket chunks filtered by source_id."""
        if self.client is None or query_vector is None:
            return []

        if not self.client.collection_exists(self.collection):
            log.debug("Collection %s does not exist; returning empty chunks", self.collection)
            return []

        query_filter = qm.Filter(
            must=[
                qm.FieldCondition(key="source_type", match=qm.MatchValue(value=self.source_type)),
                qm.FieldCondition(key="source_id", match=qm.MatchValue(value=source_id)),
            ]
        )

        try:
            if hasattr(self.client, "search"):
                hits = self.client.search(
                    collection_name=self.collection,
                    query_vector=query_vector,
                    query_filter=query_filter,
                    limit=limit,
                    with_payload=True,
                )
            else:
                res = self.client.query_points(
                    collection_name=self.collection,
                    query=query_vector,
                    query_filter=query_filter,
                    limit=limit,
                    with_payload=True,
                )
                hits = res.points
            return [
                self.normalize_chunk_payload(h.payload or {}, score=float(h.score), default_source_name=source_name)
                for h in hits
            ]
        except Exception as exc:
            log.warning("Vector retrieval failed for ticket source %s: %s", source_id, exc)
            return []

