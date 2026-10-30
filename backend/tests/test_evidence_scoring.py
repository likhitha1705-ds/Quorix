"""Tests for Phase 5 Evidence Scoring Engine (Relevance, Authority, Freshness, Directness, Confidence)."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from app.evaluation.config import EvaluationConfig, EvidenceScoringWeights
from app.evaluation.scoring import (
    AuthorityEvaluator,
    DirectnessEvaluator,
    EvidenceScoringEngine,
    FreshnessEvaluator,
    RelevanceEvaluator,
)
from app.schemas.intelligence import QueryAnalysis, QueryIntent
from app.schemas.retrieval import RetrievedChunk


def make_chunk(
    content: str,
    chunk_id: str = "c1",
    source_name: str = "Architecture Docs",
    source_type: str = "document",
    similarity_score: float = 0.85,
    keyword_score: float = 0.80,
    timestamp: datetime | None = None,
    metadata: dict | None = None,
) -> RetrievedChunk:
    return RetrievedChunk(
        chunk_id=chunk_id,
        source_id="src_1",
        source_type=source_type,
        source_name=source_name,
        content=content,
        similarity_score=similarity_score,
        keyword_score=keyword_score,
        final_score=similarity_score,
        timestamp=timestamp,
        metadata=metadata or {},
    )


def test_relevance_evaluator():
    evaluator = RelevanceEvaluator()
    qa = QueryAnalysis(
        query="What is the Redis cache TTL?",
        intent=QueryIntent.CONFIGURATION_LOOKUP,
        keywords=["redis", "cache", "ttl"],
        entities=["Redis", "TTL"],
        expected_information_type="Configuration Parameter",
        preferred_sources=["document"],
    )

    high_chunk = make_chunk("Redis cache TTL is configured to 300 seconds by default.")
    low_chunk = make_chunk("The team discussed frontend CSS layout choices.", similarity_score=0.1)

    score_high = evaluator.evaluate(high_chunk, qa)
    score_low = evaluator.evaluate(low_chunk, qa)

    assert 0.0 <= score_high <= 1.0
    assert 0.0 <= score_low <= 1.0
    assert score_high > score_low
    assert score_high >= 0.70


def test_authority_evaluator():
    evaluator = AuthorityEvaluator()

    doc_chunk = make_chunk("Architecture guide", source_name="Architecture Standard", source_type="document")
    conv_chunk = make_chunk("Team chat", source_name="Slack Channel", source_type="conversation")
    ticket_chunk = make_chunk("Bug fix", source_name="Jira Board", source_type="ticket", metadata={"status": "resolved"})
    explicit_chunk = make_chunk("Explicit", source_name="Custom", source_type="custom", metadata={"authority_score": 0.99})

    assert evaluator.evaluate(doc_chunk) >= 0.90
    assert 0.55 <= evaluator.evaluate(conv_chunk) <= 0.75
    assert evaluator.evaluate(ticket_chunk) >= 0.65
    assert evaluator.evaluate(explicit_chunk) == 0.99


def test_freshness_evaluator_decay_and_historical_discount():
    evaluator = FreshnessEvaluator()
    now = datetime.now(timezone.utc)
    old_time = now - timedelta(days=365)

    recent_chunk = make_chunk("Recent info", timestamp=now - timedelta(days=5))
    old_chunk = make_chunk("Old info", timestamp=old_time)

    config_qa = QueryAnalysis(
        query="What is the Redis TTL?",
        intent=QueryIntent.CONFIGURATION_LOOKUP,
        keywords=["redis", "ttl"],
        entities=["Redis"],
        expected_information_type="Config",
        preferred_sources=["document"],
    )

    hist_qa = QueryAnalysis(
        query="Why was Redis introduced?",
        intent=QueryIntent.HISTORICAL_REASON,
        keywords=["redis", "introduced"],
        entities=["Redis"],
        expected_information_type="Rationale",
        preferred_sources=["conversation", "document"],
    )

    recent_score = evaluator.evaluate(recent_chunk, config_qa)
    old_config_score = evaluator.evaluate(old_chunk, config_qa)
    old_hist_score = evaluator.evaluate(old_chunk, hist_qa)

    assert recent_score > old_config_score
    # Historical discount ensures historical queries suffer less penalty on older information
    assert old_hist_score > old_config_score


def test_directness_evaluator():
    evaluator = DirectnessEvaluator()
    qa = QueryAnalysis(
        query="What is the Redis cache TTL?",
        intent=QueryIntent.CONFIGURATION_LOOKUP,
        keywords=["redis", "ttl"],
        entities=["Redis", "TTL"],
        expected_information_type="Config",
        preferred_sources=["document"],
    )

    direct_chunk = make_chunk("redis ttl: 300 seconds", source_type="document")
    medium_chunk = make_chunk("We should look at the Redis configuration tomorrow.", source_type="conversation")
    low_chunk = make_chunk("Redis is an in-memory database used across our infrastructure.", source_type="document")

    d_direct = evaluator.evaluate(direct_chunk, qa)
    d_med = evaluator.evaluate(medium_chunk, qa)
    d_low = evaluator.evaluate(low_chunk, qa)

    assert d_direct > d_med
    assert d_med >= d_low
    assert d_direct >= 0.85


def test_evidence_scoring_engine_confidence_and_explanation():
    config = EvaluationConfig(
        weights=EvidenceScoringWeights(
            relevance=0.40,
            authority=0.25,
            directness=0.20,
            freshness=0.15,
        )
    )
    engine = EvidenceScoringEngine(config=config)
    qa = QueryAnalysis(
        query="What is the Redis cache TTL?",
        intent=QueryIntent.CONFIGURATION_LOOKUP,
        keywords=["redis", "ttl"],
        entities=["Redis", "TTL"],
        expected_information_type="Config",
        preferred_sources=["document"],
    )

    chunk = make_chunk(
        content="In the official architecture specification, redis ttl = 600s for session storage.",
        source_name="Architecture Specification",
        source_type="document",
        similarity_score=0.92,
        timestamp=datetime.now(timezone.utc),
    )

    evaluated = engine.score_chunk(chunk, qa)
    assert 0.0 <= evaluated.score <= 1.0
    assert evaluated.score >= 0.80
    assert evaluated.relevance_score > 0.70
    assert evaluated.authority_score >= 0.90
    assert evaluated.directness_score >= 0.85
    assert "Architecture Specification" in evaluated.explanation

