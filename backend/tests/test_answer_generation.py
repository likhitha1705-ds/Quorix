"""Unit tests for Phase 6 AnswerGenerationService and uncertainty handling."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.generation.config import GenerationConfig
from app.generation.pipeline import AnswerGenerationService
from app.schemas.evaluation import (
    Conflict,
    EvaluatedChunk,
    EvidenceDecision,
    EvidenceEvaluationResult,
    EvidenceScore,
    EvidenceSummary,
)
from app.schemas.intelligence import QueryAnalysis, QueryIntent
from app.schemas.retrieval import RetrievedChunk


def make_eval_chunk(
    chunk_id: str,
    content: str,
    source: str = "Architecture Docs",
    source_type: str = "document",
    confidence: float = 0.90,
) -> EvaluatedChunk:
    chunk = RetrievedChunk(
        chunk_id=chunk_id,
        source_id=f"src_{chunk_id}",
        source_type=source_type,
        source_name=source,
        content=content,
        similarity_score=confidence,
        keyword_score=confidence,
        final_score=confidence,
        timestamp=datetime.now(timezone.utc),
    )
    score = EvidenceScore(
        relevance_score=confidence,
        authority_score=0.90,
        freshness_score=1.0,
        directness_score=0.95,
        confidence_score=confidence,
        explanation="High authority chunk",
    )
    return EvaluatedChunk(chunk=chunk, evidence_score=score)


def make_eval_result(
    query: str,
    decision: EvidenceDecision,
    chunks: list[EvaluatedChunk] | None = None,
    conflicts: list[Conflict] | None = None,
    confidence: float = 0.90,
) -> EvidenceEvaluationResult:
    qa = QueryAnalysis(
        query=query,
        intent=QueryIntent.CONFIGURATION_LOOKUP,
        keywords=["redis", "ttl"],
        entities=["Redis", "TTL"],
        expected_information_type="Config",
        preferred_sources=["document"],
    )
    evaluated_chunks = chunks or []
    summary = EvidenceSummary(
        average_confidence=confidence,
        highest_confidence=confidence,
        lowest_confidence=confidence,
        total_evaluated_chunks=len(evaluated_chunks),
        strongest_evidence=evaluated_chunks,
        supporting_sources=[c.source for c in evaluated_chunks],
        conflicting_sources=[],
    )
    return EvidenceEvaluationResult(
        query_analysis=qa,
        evaluated_chunks=evaluated_chunks,
        evidence_summary=summary,
        conflicts=conflicts or [],
        confidence_score=confidence,
        evidence_decision=decision,
        needs_more_retrieval=False,
        remaining_budget={},
        evaluation_explanation="Evidence evaluated successfully.",
        retrieval_metrics={"retrieved_chunks": len(evaluated_chunks), "retrieval_calls": 1},
        execution_metadata={},
    )


def test_answer_generation_sufficient():
    service = AnswerGenerationService()
    c1 = make_eval_chunk("chunk_1", "redis ttl = 300 seconds for auth cache.", source="Architecture Spec")
    result = make_eval_result(
        query="What is the Redis cache TTL?",
        decision=EvidenceDecision.SUFFICIENT,
        chunks=[c1],
        confidence=0.92,
    )

    answer_res = service.generate_answer(result)

    assert answer_res.evidence_decision == EvidenceDecision.SUFFICIENT
    assert answer_res.confidence == 0.92
    assert "redis ttl = 300 seconds" in answer_res.answer.lower()
    assert len(answer_res.citations) >= 1
    assert answer_res.citations[0].chunk_id == "chunk_1"
    assert answer_res.citations[0].source_name == "Architecture Spec"

    # Verify execution metrics
    metrics = answer_res.execution_metrics
    assert metrics.response_generation_time_ms > 0
    assert metrics.total_tokens > 0
    assert metrics.estimated_cost >= 0.0


def test_answer_generation_conflicting():
    service = AnswerGenerationService()
    c1 = make_eval_chunk("c1", "redis ttl = 600 seconds", source="Architecture Guide")
    c2 = make_eval_chunk("c2", "redis ttl = 300 seconds", source="Deployment Notes")
    conflict = Conflict(
        conflicting_chunks=["c1", "c2"],
        conflicting_fields=["ttl"],
        severity="high",
        explanation="Architecture Guide specifies '600s' whereas Deployment Notes specifies '300s'.",
    )
    result = make_eval_result(
        query="What is the Redis cache TTL?",
        decision=EvidenceDecision.CONFLICTING,
        chunks=[c1, c2],
        conflicts=[conflict],
        confidence=0.85,
    )

    answer_res = service.generate_answer(result)

    assert answer_res.evidence_decision == EvidenceDecision.CONFLICTING
    assert "conflict" in answer_res.answer.lower()
    assert "600s" in answer_res.answer
    assert "300s" in answer_res.answer
    assert len(answer_res.citations) >= 1


def test_answer_generation_insufficient():
    service = AnswerGenerationService()
    c1 = make_eval_chunk("c1", "We talked about caching but no TTL was recorded.", confidence=0.45)
    result = make_eval_result(
        query="What is the Redis cache TTL?",
        decision=EvidenceDecision.INSUFFICIENT,
        chunks=[c1],
        confidence=0.45,
    )

    answer_res = service.generate_answer(result)

    assert answer_res.evidence_decision == EvidenceDecision.INSUFFICIENT
    assert "insufficient" in answer_res.answer.lower()
    assert answer_res.confidence == 0.45


def test_answer_generation_unsupported():
    service = AnswerGenerationService()
    result = make_eval_result(
        query="What is the average temperature on Neptune?",
        decision=EvidenceDecision.UNSUPPORTED,
        chunks=[],
        confidence=0.0,
    )

    answer_res = service.generate_answer(result)

    assert answer_res.evidence_decision == EvidenceDecision.UNSUPPORTED
    assert answer_res.confidence == 0.0
    assert len(answer_res.citations) == 0
    assert "no relevant documentation" in answer_res.answer.lower()
    assert "hallucination" in answer_res.answer.lower()
    # LLM should be bypassed to avoid any fabrication
    assert answer_res.execution_metrics.llm_latency_ms == 0.0

