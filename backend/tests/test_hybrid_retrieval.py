"""Unit tests for Phase 4: Hybrid Retrieval, Ranking, Deduplication, Context Builder."""
from __future__ import annotations

import hashlib
from datetime import datetime, timedelta, timezone

import pytest

from app.retrieval.adapters import (
    BaseRetrievalAdapter,
    ConversationRetrievalAdapter,
    DocumentRetrievalAdapter,
    RetrievalAdapterRegistry,
    TicketRetrievalAdapter,
)
from app.retrieval.budget import RetrievalBudgetManager
from app.retrieval.config import RankingWeights, RetrievalConfig
from app.retrieval.context_builder import ContextBuilder
from app.retrieval.deduplication import ChunkDeduplicator
from app.retrieval.engine import HybridRetrievalEngine
from app.retrieval.lexical import LexicalRetrievalEngine
from app.retrieval.ranking import RankingEngine
from app.retrieval.semantic import SemanticRetrievalEngine
from app.schemas.intelligence import QueryAnalysis, QueryDecision, QueryIntent, RankedSource
from app.schemas.retrieval import RetrievalBudget, RetrievalPlan, RetrievedChunk


class MockEmbedder:
    """Deterministic lightweight embedder for testing."""

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        # Generate 8-dimensional normalized pseudo-vector
        res = []
        for t in texts:
            h = hashlib.sha256(t.encode("utf-8")).digest()
            vec = [b / 255.0 for b in h[:8]]
            norm = sum(x * x for x in vec) ** 0.5 or 1.0
            res.append([x / norm for x in vec])
        return res

    def embed_query(self, query: str) -> list[float]:
        return self.embed_documents([query])[0]


class InMemoryAdapter(BaseRetrievalAdapter):
    """Test adapter with in-memory chunks."""

    def __init__(self, source_type: str, chunks: list[RetrievedChunk]) -> None:
        self.source_type = source_type
        self.chunks = chunks

    def retrieve(
        self,
        query: str,
        query_vector: list[float] | None,
        source_id: str,
        limit: int,
        source_name: str | None = None,
    ) -> list[RetrievedChunk]:
        matched = [c for c in self.chunks if c.source_id == source_id]
        return matched[:limit]


def make_chunk(
    chunk_id: str,
    source_id: str,
    source_type: str,
    content: str,
    sim_score: float = 0.8,
    kw_score: float = 0.5,
    ts: datetime | None = None,
) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=chunk_id,
        source_id=source_id,
        source_type=source_type,
        source_name=f"Source {source_id}",
        content=content,
        similarity_score=sim_score,
        keyword_score=kw_score,
        final_score=sim_score,
        timestamp=ts or datetime.now(timezone.utc),
        metadata={"source_reference": f"{source_id}/{chunk_id}.md", "authority_level": 0.85},
    )


def test_ranking_engine_fused_score_and_sorting():
    weights = RankingWeights(semantic=0.50, keyword=0.30, authority=0.12, freshness=0.08)
    engine = RankingEngine(weights=weights)

    chunk_a = make_chunk("c1", "s1", "document", "high relevance", sim_score=0.9, kw_score=0.8)
    chunk_b = make_chunk("c2", "s1", "document", "medium relevance", sim_score=0.4, kw_score=0.2)

    ranked = engine.rank([chunk_b, chunk_a])
    # Highest final score must be first
    assert ranked[0].chunk_id == "c1"
    assert ranked[1].chunk_id == "c2"
    assert ranked[0].final_score > ranked[1].final_score


def test_deduplication_exact_and_content_hash():
    dedup = ChunkDeduplicator()

    chunk_1 = make_chunk("c1", "s1", "document", "Redis caching was introduced for performance.", sim_score=0.9)
    # Identical content but different chunk_id
    chunk_2 = make_chunk("c2", "s2", "conversation", "  Redis caching was introduced for performance.  ", sim_score=0.7)
    # Distinct chunk
    chunk_3 = make_chunk("c3", "s1", "document", "PostgreSQL schema initialization details.", sim_score=0.8)

    results = dedup.deduplicate([chunk_1, chunk_2, chunk_3])
    # chunk_2 should be removed as duplicate of chunk_1, keeping chunk_1 (higher score)
    assert len(results) == 2
    assert results[0].chunk_id == "c1"
    assert results[1].chunk_id == "c3"
    # Metadata on chunk_1 should preserve alternate reference to chunk_2
    assert "alternate_references" in results[0].metadata
    assert results[0].metadata["alternate_references"][0]["chunk_id"] == "c2"


def test_context_builder_chunk_and_token_limits():
    builder = ContextBuilder(chars_per_token=4.0)

    # 4 chunks of 40 characters each = ~10 tokens each
    chunks = [
        make_chunk(f"c{i}", "s1", "document", "x" * 40)
        for i in range(4)
    ]

    # Test chunk limit enforcement (limit to 2 chunks)
    plan_chunk_limit = RetrievalPlan(
        selected_sources=["s1"],
        retrieval_budget=RetrievalBudget(max_sources=1, max_chunks=2, max_context_tokens=1000, max_retrieval_calls=1),
        chunk_limit=2,
        token_limit=1000,
        retrieval_call_limit=1,
    )
    bounded, tokens = builder.build_context(chunks, plan_chunk_limit)
    assert len(bounded) == 2

    # Test token limit enforcement (limit to 25 tokens, each chunk is 10 tokens -> max 2 chunks)
    plan_token_limit = RetrievalPlan(
        selected_sources=["s1"],
        retrieval_budget=RetrievalBudget(max_sources=1, max_chunks=10, max_context_tokens=25, max_retrieval_calls=1),
        chunk_limit=10,
        token_limit=25,
        retrieval_call_limit=1,
    )
    bounded, tokens = builder.build_context(chunks, plan_token_limit)
    assert len(bounded) == 2
    assert tokens <= 25


def test_lexical_engine_bm25_scoring():
    engine = LexicalRetrievalEngine()
    chunks = [
        make_chunk("c1", "s1", "document", "Redis cache connection pool settings"),
        make_chunk("c2", "s1", "document", "PostgreSQL database table migration index"),
        make_chunk("c3", "s1", "document", "FastAPI route handling and endpoints"),
    ]

    scored, latency = engine.search(
        query="Redis cache",
        keywords=["redis", "cache"],
        candidate_chunks=chunks,
    )

    # Chunk with "Redis cache" must have the highest keyword_score
    c1 = next(c for c in scored if c.chunk_id == "c1")
    c2 = next(c for c in scored if c.chunk_id == "c2")
    assert c1.keyword_score > c2.keyword_score


def test_single_source_hybrid_retrieval():
    doc_chunks = [
        make_chunk("doc_1", "src_documents", "document", "Redis was introduced to reduce DB query latency."),
        make_chunk("doc_2", "src_documents", "document", "Configuration options for Redis cluster."),
    ]
    registry = RetrievalAdapterRegistry([
        InMemoryAdapter("document", doc_chunks),
        InMemoryAdapter("conversation", []),
        InMemoryAdapter("ticket", []),
    ])

    config = RetrievalConfig(max_chunks=5)
    engine = HybridRetrievalEngine(
        config=config,
        embedder=MockEmbedder(),
        semantic_engine=SemanticRetrievalEngine(embedder=MockEmbedder(), adapter_registry=registry),
    )

    decision = QueryDecision(
        query_analysis=QueryAnalysis(
            query="Why was Redis caching introduced?",
            intent=QueryIntent.HISTORICAL_REASON,
            keywords=["redis", "caching", "introduced"],
            entities=["Redis"],
            expected_information_type="decision_history",
            preferred_sources=["documents"],
        ),
        selected_sources=[
            RankedSource(
                source_id="src_documents",
                source_name="Technical Documents",
                source_type="document",
                relevance_score=0.8,
                authority_score=0.85,
                freshness_score=1.0,
                expected_directness_score=0.8,
                overall_score=0.85,
                selection_reason="Selected",
                is_selected=True,
            )
        ],
    )

    result = engine.retrieve(decision)
    assert len(result.retrieved_chunks) == 2
    assert all(c.source_id == "src_documents" for c in result.retrieved_chunks)
    assert result.retrieval_metrics.retrieval_calls == 1
    assert result.retrieval_metrics.retrieved_chunks == 2


def test_multi_source_hybrid_retrieval():
    doc_chunks = [
        make_chunk("doc_1", "src_documents", "document", "Redis documentation on architectural choices."),
    ]
    conv_chunks = [
        make_chunk("conv_1", "src_conversations", "conversation", "Team discussion on Redis caching rationale."),
    ]
    registry = RetrievalAdapterRegistry([
        InMemoryAdapter("document", doc_chunks),
        InMemoryAdapter("conversation", conv_chunks),
        InMemoryAdapter("ticket", []),
    ])

    config = RetrievalConfig(max_chunks=5)
    engine = HybridRetrievalEngine(
        config=config,
        embedder=MockEmbedder(),
        semantic_engine=SemanticRetrievalEngine(embedder=MockEmbedder(), adapter_registry=registry),
    )

    decision = QueryDecision(
        query_analysis=QueryAnalysis(
            query="Why was Redis caching introduced?",
            intent=QueryIntent.HISTORICAL_REASON,
            keywords=["redis", "caching", "introduced"],
            entities=["Redis"],
            expected_information_type="decision_history",
            preferred_sources=["documents", "conversations"],
        ),
        selected_sources=[
            RankedSource(
                source_id="src_documents",
                source_name="Technical Documents",
                source_type="document",
                relevance_score=0.8,
                authority_score=0.85,
                freshness_score=1.0,
                expected_directness_score=0.8,
                overall_score=0.85,
                selection_reason="Selected",
                is_selected=True,
            ),
            RankedSource(
                source_id="src_conversations",
                source_name="Engineering Conversations",
                source_type="conversation",
                relevance_score=0.8,
                authority_score=0.5,
                freshness_score=1.0,
                expected_directness_score=0.9,
                overall_score=0.80,
                selection_reason="Selected",
                is_selected=True,
            ),
        ],
    )

    result = engine.retrieve(decision)
    source_ids = {c.source_id for c in result.retrieved_chunks}
    assert "src_documents" in source_ids
    assert "src_conversations" in source_ids
    assert result.retrieval_metrics.retrieval_calls == 2


def test_empty_retrieval_result():
    engine = HybridRetrievalEngine(embedder=MockEmbedder())
    # Decision with zero selected sources (e.g. non-matching query)
    decision = QueryDecision(
        query_analysis=QueryAnalysis(
            query="Unrelated cooking recipe",
            intent=QueryIntent.GENERAL_INFORMATION,
            keywords=["cooking"],
            entities=[],
            expected_information_type="general_summary",
            preferred_sources=["multi_source"],
        ),
        selected_sources=[],
    )

    result = engine.retrieve(decision)
    assert len(result.retrieved_chunks) == 0
    assert result.retrieval_metrics.retrieved_chunks == 0
    assert result.retrieval_metrics.retrieval_calls == 0
    assert result.retrieval_plan.selected_sources == []
