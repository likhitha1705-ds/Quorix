"""Lexical retrieval engine using BM25 keyword scoring over candidate chunks."""
from __future__ import annotations

import logging
import re
import time
from typing import Any

from qdrant_client import QdrantClient
from qdrant_client.http import models as qm
from rank_bm25 import BM25Okapi

from app.schemas.intelligence import RankedSource
from app.schemas.retrieval import RetrievedChunk

log = logging.getLogger(__name__)


class LexicalRetrievalEngine:
    """Performs BM25 lexical keyword retrieval over chunk text."""

    def __init__(
        self,
        client: QdrantClient | None = None,
        collection: str = "quorix_chunks",
        k1: float = 1.5,
        b: float = 0.75,
    ) -> None:
        self.client = client
        self.collection = collection
        self.k1 = k1
        self.b = b

    def search(
        self,
        query: str,
        keywords: list[str],
        candidate_chunks: list[RetrievedChunk],
        selected_sources: list[RankedSource] | None = None,
        limit: int = 10,
    ) -> tuple[list[RetrievedChunk], float]:
        """Perform BM25 keyword search over candidate chunks, updating their keyword_score.

        Returns (scored_chunks, latency_ms).
        """
        start_time = time.perf_counter()

        # Combine passed candidates with any additional chunks fetched from Qdrant scroll
        pool = list(candidate_chunks)
        if self.client and selected_sources:
            scrolled = self._scroll_source_chunks(selected_sources, existing_ids={c.chunk_id for c in pool})
            pool.extend(scrolled)

        if not pool:
            return [], round((time.perf_counter() - start_time) * 1000, 2)

        # Prepare tokens for BM25
        tokenized_corpus = [self._tokenize(c.content) for c in pool]
        query_tokens = [k.lower() for k in keywords] if keywords else self._tokenize(query)

        if not query_tokens:
            return pool, round((time.perf_counter() - start_time) * 1000, 2)

        # Run BM25
        bm25 = BM25Okapi(tokenized_corpus, k1=self.k1, b=self.b)
        raw_scores = bm25.get_scores(query_tokens)
        max_score = float(max(raw_scores)) if len(raw_scores) > 0 else 0.0

        scored_chunks: list[RetrievedChunk] = []
        for chunk, score in zip(pool, raw_scores):
            norm_score = float(score / max_score) if max_score > 0 else 0.0
            updated_chunk = chunk.model_copy(
                update={"keyword_score": round(max(0.0, min(1.0, norm_score)), 4)}
            )
            scored_chunks.append(updated_chunk)

        # Sort by keyword score descending
        scored_chunks.sort(key=lambda c: c.keyword_score, reverse=True)
        latency_ms = round((time.perf_counter() - start_time) * 1000, 2)
        log.debug("BM25 lexical scoring evaluated %d chunks in %.2fms", len(scored_chunks), latency_ms)
        return scored_chunks[:limit], latency_ms

    def _scroll_source_chunks(
        self,
        selected_sources: list[RankedSource],
        existing_ids: set[str],
        max_scroll: int = 30,
    ) -> list[RetrievedChunk]:
        """Scroll additional chunks from Qdrant for selected sources to enrich the lexical pool."""
        if not self.client or not self.client.collection_exists(self.collection):
            return []

        source_ids = [s.source_id for s in selected_sources]
        query_filter = qm.Filter(
            must=[qm.FieldCondition(key="source_id", match=qm.MatchAny(any=source_ids))]
        )

        try:
            hits, _ = self.client.scroll(
                collection_name=self.collection,
                scroll_filter=query_filter,
                limit=max_scroll,
                with_payload=True,
            )
            scrolled_chunks: list[RetrievedChunk] = []
            for hit in hits:
                cid = hit.payload.get("chunk_id", str(hit.id)) if hit.payload else str(hit.id)
                if cid not in existing_ids:
                    existing_ids.add(cid)
                    scrolled_chunks.append(
                        RetrievedChunk(
                            chunk_id=cid,
                            source_id=hit.payload.get("source_id", "unknown"),
                            source_type=hit.payload.get("source_type", "document"),
                            source_name=hit.payload.get("title") or hit.payload.get("source_id", "Source"),
                            content=hit.payload.get("text", ""),
                            similarity_score=0.0,
                            keyword_score=0.0,
                            final_score=0.0,
                            metadata=dict(hit.payload or {}),
                        )
                    )
            return scrolled_chunks
        except Exception as exc:
            log.warning("Scroll query for lexical search failed: %s", exc)
            return []

    @staticmethod
    def _tokenize(text: str) -> list[str]:
        return [t.lower() for t in re.findall(r"[A-Za-z0-9_\-]+", text) if len(t) > 1]

