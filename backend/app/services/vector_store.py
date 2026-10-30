"""Qdrant collection management and chunk upserts."""
from __future__ import annotations

import logging

from qdrant_client import QdrantClient
from qdrant_client.http import models as qm

from app.schemas.source import Chunk

log = logging.getLogger(__name__)

KEYWORD_INDEXES = ("source_id", "source_type", "document_id", "status")
DATETIME_INDEXES = ("created_at", "updated_at")
UPSERT_BATCH = 64


class VectorDimensionMismatch(RuntimeError):
    pass


class VectorStore:
    def __init__(self, client: QdrantClient, collection: str) -> None:
        self.client = client
        self.collection = collection

    def ensure_collection(self, dimension: int) -> bool:
        """Create the collection only if missing. Returns True when created."""
        created = False
        if not self.client.collection_exists(self.collection):
            self.client.create_collection(
                collection_name=self.collection,
                vectors_config=qm.VectorParams(size=dimension, distance=qm.Distance.COSINE),
            )
            created = True
            log.info("Created Qdrant collection %s (dim=%d, cosine)", self.collection, dimension)
        else:
            info = self.client.get_collection(self.collection)
            vectors = info.config.params.vectors
            existing = vectors.size if isinstance(vectors, qm.VectorParams) else None
            if existing != dimension:
                raise VectorDimensionMismatch(
                    f"Collection '{self.collection}' has vector size {existing}, but the "
                    f"embedding model produces {dimension}. Re-run with --rebuild-index."
                )
        self._ensure_payload_indexes()
        return created

    def _ensure_payload_indexes(self) -> None:
        existing = set(self.client.get_collection(self.collection).payload_schema or {})
        for field in KEYWORD_INDEXES:
            if field not in existing:
                self.client.create_payload_index(
                    self.collection, field, qm.PayloadSchemaType.KEYWORD
                )
        for field in DATETIME_INDEXES:
            if field not in existing:
                self.client.create_payload_index(
                    self.collection, field, qm.PayloadSchemaType.DATETIME
                )

    def delete_collection(self) -> None:
        if self.client.collection_exists(self.collection):
            self.client.delete_collection(self.collection)

    def delete_document(self, document_id: str) -> None:
        """Remove all chunks of a document (handles documents that shrank)."""
        self.client.delete(
            self.collection,
            points_selector=qm.FilterSelector(
                filter=qm.Filter(
                    must=[qm.FieldCondition(key="document_id", match=qm.MatchValue(value=document_id))]
                )
            ),
            wait=True,
        )

    def upsert_chunks(self, chunks: list[Chunk], vectors: list[list[float]]) -> None:
        if len(chunks) != len(vectors):
            raise ValueError("chunks and vectors length mismatch")
        for i in range(0, len(chunks), UPSERT_BATCH):
            batch = [
                qm.PointStruct(id=c.point_id, vector=v, payload=c.to_payload())
                for c, v in zip(chunks[i : i + UPSERT_BATCH], vectors[i : i + UPSERT_BATCH])
            ]
            self.client.upsert(self.collection, points=batch, wait=True)

    def count(self) -> int:
        return self.client.count(self.collection, exact=True).count
