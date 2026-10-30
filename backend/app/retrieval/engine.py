"""Hybrid retrieval engine orchestrating budget management, semantic & lexical search, ranking, and deduplication."""
from __future__ import annotations

import logging
import time
from typing import Any

from qdrant_client import QdrantClient

from app.core.config import get_settings
from app.db.qdrant import get_qdrant_client
from app.retrieval.budget import RetrievalBudgetManager
from app.retrieval.config import RetrievalConfig
from app.retrieval.context_builder import ContextBuilder
from app.retrieval.deduplication import ChunkDeduplicator
from app.retrieval.lexical import LexicalRetrievalEngine
from app.retrieval.metrics import RetrievalMetricsTracker
from app.retrieval.ranking import RankingEngine
from app.retrieval.semantic import SemanticRetrievalEngine
from app.schemas.intelligence import QueryDecision
from app.schemas.retrieval import RetrievalPlan, RetrievalResult, RetrievedChunk
from app.services.embedding import EmbeddingService

log = logging.getLogger(__name__)


class HybridRetrievalEngine:
    """Intelligently retrieves and merges candidate chunks across semantic and lexical modalities."""

    def __init__(
        self,
        config: RetrievalConfig | None = None,
        client: QdrantClient | None = None,
        embedder: Any = None,
        budget_manager: RetrievalBudgetManager | None = None,
        semantic_engine: SemanticRetrievalEngine | None = None,
        lexical_engine: LexicalRetrievalEngine | None = None,
        ranking_engine: RankingEngine | None = None,
        deduplicator: ChunkDeduplicator | None = None,
        context_builder: ContextBuilder | None = None,
    ) -> None:
        self.config = config or RetrievalConfig()
        settings = get_settings()

        # Resolve Qdrant client
        if client is not None:
            self.client = client
        else:
            try:
                if settings.qdrant_url:
                    self.client = get_qdrant_client()
                else:
                    self.client = QdrantClient(":memory:")
            except Exception as exc:
                log.warning("Could not connect to Qdrant cluster (%s); using in-memory Qdrant instance", exc)
                self.client = QdrantClient(":memory:")

        # Resolve embedder
        if embedder is not None:
            self.embedder = embedder
        else:
            self.embedder = EmbeddingService(settings.embedding_model_name)

        # Initialize modular pipeline components
        self.budget_manager = budget_manager or RetrievalBudgetManager(config=self.config)
        self.semantic_engine = semantic_engine or SemanticRetrievalEngine(
            client=self.client,
            embedder=self.embedder,
            collection=self.config.qdrant_collection,
        )
        self.lexical_engine = lexical_engine or LexicalRetrievalEngine(
            client=self.client,
            collection=self.config.qdrant_collection,
        )
        self.ranking_engine = ranking_engine or RankingEngine(
            weights=self.config.ranking_weights,
            freshness_half_life_days=self.config.freshness_half_life_days,
            historical_penalty_discount=self.config.historical_penalty_discount,
        )
        self.deduplicator = deduplicator or ChunkDeduplicator()
        self.context_builder = context_builder or ContextBuilder(chars_per_token=self.config.chars_per_token)

    def retrieve(self, decision: QueryDecision) -> RetrievalResult:
        """Execute the hybrid retrieval pipeline given a Phase 3 QueryDecision."""
        start_time = time.perf_counter()
        query = decision.query_analysis.query
        selected_sources = decision.selected_sources
        skipped_source_ids = [s.source_id for s in decision.skipped_sources]

        # Step 1: Retrieval Budget Manager
        plan = self.budget_manager.create_plan(decision)

        # Early return if no sources were selected
        if not plan.selected_sources:
            log.info("No sources selected for retrieval query %r; returning empty context", query)
            total_time_ms = round((time.perf_counter() - start_time) * 1000, 2)
            empty_metrics = RetrievalMetricsTracker.build_metrics(
                plan=plan,
                calls_made=0,
                chunks_retrieved=0,
                estimated_tokens=0,
                execution_time_ms=total_time_ms,
                selected_sources=[],
                skipped_sources=skipped_source_ids,
            )
            return RetrievalResult(
                query_analysis=decision.query_analysis,
                selected_sources=[],
                retrieval_plan=plan,
                retrieved_chunks=[],
                retrieval_metrics=empty_metrics,
                execution_metadata={"latency_ms": total_time_ms, "status": "no_sources_selected"},
            )

        # Over-fetch limit per source to provide candidate pool for hybrid fusion and deduplication
        pool_limit = max(plan.chunk_limit, plan.chunk_limit * self.config.candidate_pool_multiplier)
        limit_per_source = {
            src_id: count * self.config.candidate_pool_multiplier
            for src_id, count in plan.retrieval_budget.allocated_chunks_per_source.items()
        }

        # Step 3: Semantic Retrieval (Qdrant)
        semantic_chunks, qdrant_latency_ms = self.semantic_engine.search(
            query=query,
            selected_sources=selected_sources,
            limit_per_source=limit_per_source,
            total_limit=pool_limit,
        )

        # Step 4: Lexical Retrieval (BM25)
        lexical_chunks, keyword_latency_ms = self.lexical_engine.search(
            query=query,
            keywords=decision.query_analysis.keywords,
            candidate_chunks=semantic_chunks,
            selected_sources=selected_sources,
            limit=pool_limit,
        )

        # Step 5: Merge and fuse chunk pools
        fused_pool = self._merge_chunk_pools(semantic_chunks, lexical_chunks)

        # Step 7: Ranking Engine
        source_authority_map = {s.source_id: s.authority_score for s in selected_sources}
        ranked_chunks = self.ranking_engine.rank(
            chunks=fused_pool,
            intent=decision.query_analysis.intent,
            source_authority_map=source_authority_map,
        )

        # Step 8: Deduplication
        deduped_chunks = self.deduplicator.deduplicate(ranked_chunks)

        # Step 9: Context Builder
        final_chunks, total_tokens = self.context_builder.build_context(deduped_chunks, plan)

        total_time_ms = round((time.perf_counter() - start_time) * 1000, 2)
        retrieval_calls = len(plan.selected_sources)

        # Step 10: Metrics
        metrics = RetrievalMetricsTracker.build_metrics(
            plan=plan,
            calls_made=retrieval_calls,
            chunks_retrieved=len(final_chunks),
            estimated_tokens=total_tokens,
            execution_time_ms=total_time_ms,
            selected_sources=plan.selected_sources,
            skipped_sources=skipped_source_ids,
        )

        # Step 13: Structured Logging
        log.info(
            "Hybrid retrieval completed in %.2fms | Query: %r | Selected Sources: %s | "
            "Plan: max_chunks=%d, max_tokens=%d | Qdrant latency: %.2fms | "
            "Keyword latency: %.2fms | Chunks retrieved: %d | Budget consumed: %s",
            total_time_ms,
            query,
            plan.selected_sources,
            plan.chunk_limit,
            plan.token_limit,
            qdrant_latency_ms,
            keyword_latency_ms,
            len(final_chunks),
            metrics.retrieval_budget_consumed,
        )

        # Reusable result for Phase 5 handoff
        return RetrievalResult(
            query_analysis=decision.query_analysis,
            selected_sources=selected_sources,
            retrieval_plan=plan,
            retrieved_chunks=final_chunks,
            retrieval_metrics=metrics,
            execution_metadata={
                "qdrant_latency_ms": qdrant_latency_ms,
                "keyword_latency_ms": keyword_latency_ms,
                "total_time_ms": total_time_ms,
            },
        )

    @staticmethod
    def _merge_chunk_pools(
        semantic_chunks: list[RetrievedChunk],
        lexical_chunks: list[RetrievedChunk],
    ) -> list[RetrievedChunk]:
        """Merge semantic and lexical candidate chunks by chunk_id, fusing their scores."""
        merged: dict[str, RetrievedChunk] = {}

        for c in semantic_chunks:
            merged[c.chunk_id] = c

        for c in lexical_chunks:
            if c.chunk_id in merged:
                existing = merged[c.chunk_id]
                # Preserve both similarity_score and keyword_score
                merged[c.chunk_id] = existing.model_copy(
                    update={"keyword_score": c.keyword_score}
                )
            else:
                merged[c.chunk_id] = c

        return list(merged.values())

