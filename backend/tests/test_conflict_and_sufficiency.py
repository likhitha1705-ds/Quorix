"""Tests for Phase 5 Conflict Detection, Evidence Aggregation, and Sufficiency Evaluation."""
from __future__ import annotations

from datetime import datetime, timezone

from app.evaluation.aggregation import EvidenceAggregator
from app.evaluation.config import EvaluationConfig
from app.evaluation.conflict_detection import ConflictDetector
from app.evaluation.scoring import EvidenceScoringEngine
from app.evaluation.sufficiency import SufficiencyChecker
from app.schemas.evaluation import EvaluatedChunk, EvidenceDecision, EvidenceScore
from app.schemas.intelligence import QueryAnalysis, QueryIntent
from app.schemas.retrieval import RetrievalBudget, RetrievalMetrics, RetrievalPlan, RetrievedChunk


def make_eval_chunk(
    chunk_id: str,
    content: str,
    source: str = "Architecture Docs",
    confidence: float = 0.85,
    directness: float = 0.90,
    authority: float = 0.90,
) -> EvaluatedChunk:
    chunk = RetrievedChunk(
        chunk_id=chunk_id,
        source_id=f"src_{chunk_id}",
        source_type="document",
        source_name=source,
        content=content,
        similarity_score=confidence,
        keyword_score=confidence,
        final_score=confidence,
        timestamp=datetime.now(timezone.utc),
    )
    score = EvidenceScore(
        relevance_score=confidence,
        authority_score=authority,
        freshness_score=0.90,
        directness_score=directness,
        confidence_score=confidence,
        explanation=f"Evaluated chunk {chunk_id}",
    )
    return EvaluatedChunk(chunk=chunk, evidence_score=score)


def test_conflict_detection_config_discrepancy():
    detector = ConflictDetector()

    c1 = make_eval_chunk("c1", "redis ttl = 600 seconds for auth tokens", source="Architecture Guide", confidence=0.88)
    c2 = make_eval_chunk("c2", "redis ttl = 300 seconds for auth tokens", source="Team Slack", confidence=0.75)

    conflicts = detector.detect([c1, c2])
    assert len(conflicts) == 1
    conflict = conflicts[0]
    assert "ttl" in conflict.conflicting_fields
    assert "c1" in conflict.conflicting_chunks
    assert "c2" in conflict.conflicting_chunks
    assert conflict.severity == "high"
    assert "600s" in conflict.explanation and "300s" in conflict.explanation


def test_conflict_detection_architectural_discrepancy():
    detector = ConflictDetector()

    c1 = make_eval_chunk("c1", "We are using kafka for event streaming and queueing.", confidence=0.80)
    c2 = make_eval_chunk("c2", "We chose rabbitmq for event streaming in the latest sprint.", confidence=0.75)

    conflicts = detector.detect([c1, c2])
    assert len(conflicts) == 1
    assert "message_broker" in conflicts[0].conflicting_fields
    assert "KAFKA" in conflicts[0].explanation
    assert "RABBITMQ" in conflicts[0].explanation


def test_conflict_detection_no_conflict_when_agreeing():
    detector = ConflictDetector()

    c1 = make_eval_chunk("c1", "redis ttl = 300 seconds", confidence=0.85)
    c2 = make_eval_chunk("c2", "redis ttl = 300s verified in staging", confidence=0.80)

    conflicts = detector.detect([c1, c2])
    assert len(conflicts) == 0


def test_evidence_aggregator():
    aggregator = EvidenceAggregator()
    c1 = make_eval_chunk("c1", "content 1", confidence=0.90)
    c2 = make_eval_chunk("c2", "content 2", confidence=0.70)
    c3 = make_eval_chunk("c3", "content 3", confidence=0.50)

    summary = aggregator.aggregate([c1, c2, c3], conflicts=[])
    assert summary.total_evaluated_chunks == 3
    assert summary.highest_confidence == 0.90
    assert summary.lowest_confidence == 0.50
    assert round(summary.average_confidence, 2) == 0.70
    assert len(summary.strongest_evidence) == 3
    assert summary.strongest_evidence[0].chunk_id == "c1"


def test_sufficiency_checker_sufficient():
    checker = SufficiencyChecker(EvaluationConfig(sufficient_threshold=0.65))
    qa = QueryAnalysis(
        query="What is the Redis cache TTL?",
        intent=QueryIntent.CONFIGURATION_LOOKUP,
        keywords=["redis", "ttl"],
        entities=["Redis", "TTL"],
        expected_information_type="Config",
        preferred_sources=["document"],
    )

    c1 = make_eval_chunk("c1", "redis ttl = 300 seconds", confidence=0.88, directness=0.95)
    summary = EvidenceAggregator().aggregate([c1], conflicts=[])
    plan = RetrievalPlan(
        selected_sources=["document"],
        retrieval_budget=RetrievalBudget(),
        chunk_limit=10,
        token_limit=4000,
        retrieval_call_limit=3,
    )
    metrics = RetrievalMetrics(retrieved_chunks=1, retrieval_calls=1, estimated_tokens=100)

    decision, loop_dec, explanation = checker.evaluate(qa, [c1], [], summary, plan, metrics)

    assert decision == EvidenceDecision.SUFFICIENT
    assert loop_dec.needs_more_retrieval is False
    assert "sufficient" in explanation.lower()


def test_sufficiency_checker_insufficient_with_loop():
    checker = SufficiencyChecker(EvaluationConfig(sufficient_threshold=0.65))
    qa = QueryAnalysis(
        query="What is the Redis cache TTL?",
        intent=QueryIntent.CONFIGURATION_LOOKUP,
        keywords=["redis", "ttl"],
        entities=["Redis", "TTL"],
        expected_information_type="Config",
        preferred_sources=["document"],
    )

    # Low confidence chunk without direct answer
    c1 = make_eval_chunk("c1", "Redis might have a cache time somewhere", confidence=0.45, directness=0.30)
    summary = EvidenceAggregator().aggregate([c1], conflicts=[])
    plan = RetrievalPlan(
        selected_sources=["document"],
        retrieval_budget=RetrievalBudget(),
        chunk_limit=10,
        token_limit=4000,
        retrieval_call_limit=3,
    )
    metrics = RetrievalMetrics(retrieved_chunks=1, retrieval_calls=1, estimated_tokens=100)

    decision, loop_dec, explanation = checker.evaluate(qa, [c1], [], summary, plan, metrics)

    assert decision == EvidenceDecision.INSUFFICIENT
    # Budget remaining -> needs_more_retrieval should be True
    assert loop_dec.needs_more_retrieval is True
    assert loop_dec.remaining_budget["chunks_remaining"] == 9
    assert loop_dec.remaining_budget["calls_remaining"] == 2


def test_sufficiency_checker_conflicting():
    checker = SufficiencyChecker(EvaluationConfig(conflict_dominance_ratio=0.50))
    detector = ConflictDetector()
    qa = QueryAnalysis(
        query="What is the Redis cache TTL?",
        intent=QueryIntent.CONFIGURATION_LOOKUP,
        keywords=["redis", "ttl"],
        entities=["Redis", "TTL"],
        expected_information_type="Config",
        preferred_sources=["document"],
    )

    c1 = make_eval_chunk("c1", "redis ttl = 600 seconds", confidence=0.85, directness=0.90)
    c2 = make_eval_chunk("c2", "redis ttl = 300 seconds", confidence=0.82, directness=0.90)
    conflicts = detector.detect([c1, c2])
    summary = EvidenceAggregator().aggregate([c1, c2], conflicts=conflicts)

    plan = RetrievalPlan(
        selected_sources=["document"],
        retrieval_budget=RetrievalBudget(),
        chunk_limit=10,
        token_limit=4000,
        retrieval_call_limit=3,
    )
    metrics = RetrievalMetrics(retrieved_chunks=2, retrieval_calls=1, estimated_tokens=200)

    decision, loop_dec, explanation = checker.evaluate(qa, [c1, c2], conflicts, summary, plan, metrics)

    assert decision == EvidenceDecision.CONFLICTING
    assert loop_dec.needs_more_retrieval is True
    assert "Conflict detected" in explanation


def test_sufficiency_checker_unsupported():
    checker = SufficiencyChecker(EvaluationConfig(unsupported_threshold=0.20))
    qa = QueryAnalysis(
        query="What is the weather on Mars?",
        intent=QueryIntent.GENERAL_INFORMATION,
        keywords=["weather", "mars"],
        entities=["Mars"],
        expected_information_type="General",
        preferred_sources=["document"],
    )

    summary = EvidenceAggregator().aggregate([], conflicts=[])
    plan = RetrievalPlan(
        selected_sources=[],
        retrieval_budget=RetrievalBudget(),
        chunk_limit=10,
        token_limit=4000,
        retrieval_call_limit=3,
    )
    metrics = RetrievalMetrics(retrieved_chunks=0, retrieval_calls=0, estimated_tokens=0)

    decision, loop_dec, explanation = checker.evaluate(qa, [], [], summary, plan, metrics)

    assert decision == EvidenceDecision.UNSUPPORTED
    assert "unsupported" in explanation.lower()

