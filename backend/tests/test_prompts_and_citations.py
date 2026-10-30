"""Unit tests for Phase 6 PromptBuilder and CitationEngine."""
from __future__ import annotations

from datetime import datetime, timezone

import pytest

from app.generation.citations import CitationEngine
from app.generation.prompts import PromptBuilder
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
    query: str = "What is the Redis cache TTL?",
    decision: EvidenceDecision = EvidenceDecision.SUFFICIENT,
    chunks: list[EvaluatedChunk] | None = None,
    conflicts: list[Conflict] | None = None,
    confidence: float = 0.92,
) -> EvidenceEvaluationResult:
    qa = QueryAnalysis(
        query=query,
        intent=QueryIntent.CONFIGURATION_LOOKUP,
        keywords=["redis", "ttl"],
        entities=["Redis", "TTL"],
        expected_information_type="Configuration Parameter",
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
        evaluation_explanation="Evidence evaluation completed.",
        retrieval_metrics={"retrieved_chunks": len(evaluated_chunks)},
        execution_metadata={},
    )


def test_prompt_builder_system_prompt():
    system_prompt = PromptBuilder.get_system_prompt()
    assert "Quorix Grounded Answer Generation Engine" in system_prompt
    assert "STRICT EVIDENCE GROUNDING" in system_prompt
    assert "NO HALLUCINATION" in system_prompt
    assert "INLINE CITATIONS" in system_prompt


def test_prompt_builder_user_prompt_sufficient():
    c1 = make_eval_chunk("c1", "redis ttl = 300 seconds", source="Cache Architecture")
    result = make_eval_result(chunks=[c1], decision=EvidenceDecision.SUFFICIENT)

    user_prompt = PromptBuilder.build_user_prompt(result)
    assert 'USER QUERY: "What is the Redis cache TTL?"' in user_prompt
    assert "EVALUATION DECISION: SUFFICIENT" in user_prompt
    assert "[c1]" in user_prompt
    assert "Cache Architecture" in user_prompt
    assert "redis ttl = 300 seconds" in user_prompt
    assert "The evidence is SUFFICIENT" in user_prompt


def test_prompt_builder_user_prompt_conflicts():
    c1 = make_eval_chunk("c1", "redis ttl = 600 seconds", source="Arch Doc")
    c2 = make_eval_chunk("c2", "redis ttl = 300 seconds", source="Chat")
    conflict = Conflict(
        conflicting_chunks=["c1", "c2"],
        conflicting_fields=["ttl"],
        severity="high",
        explanation="Arch Doc specifies 600s whereas Chat specifies 300s.",
    )
    result = make_eval_result(
        chunks=[c1, c2],
        conflicts=[conflict],
        decision=EvidenceDecision.CONFLICTING,
    )

    user_prompt = PromptBuilder.build_user_prompt(result)
    assert "EVALUATION DECISION: CONFLICTING" in user_prompt
    assert "Conflict 1 (Severity: HIGH on fields ['ttl'])" in user_prompt
    assert "The evidence contains CONFLICTING claims" in user_prompt


def test_citation_engine_bracket_extraction():
    c1 = make_eval_chunk("chunk_doc_1", "Official spec: Redis TTL is 300s.", source="Technical Guide")
    c2 = make_eval_chunk("chunk_conv_1", "Discussion on cache eviction policies.", source="Slack Eng")
    result = make_eval_result(chunks=[c1, c2])

    text = "According to official documentation, the Redis TTL is 300s [chunk_doc_1]."
    engine = CitationEngine()
    citations = engine.extract_citations(text, result)

    assert len(citations) == 1
    assert citations[0].chunk_id == "chunk_doc_1"
    assert citations[0].source_name == "Technical Guide"
    assert citations[0].source_type == "document"
    assert "Redis TTL is 300s" in (citations[0].quote or "")


def test_citation_engine_prevents_hallucinated_citations():
    c1 = make_eval_chunk("chunk_doc_1", "Real documentation content.")
    result = make_eval_result(chunks=[c1])

    # Text contains references to non-existent chunks (e.g. hallucinated chunk IDs)
    text = "We also checked [invented_chunk_99] and [fake_source]."
    engine = CitationEngine()
    citations = engine.extract_citations(text, result)

    # Hallucinated IDs are discarded; fallback grounds to valid c1
    cited_ids = [cit.chunk_id for cit in citations]
    assert "invented_chunk_99" not in cited_ids
    assert "fake_source" not in cited_ids


def test_citation_engine_fallback_for_plain_text():
    c1 = make_eval_chunk("chunk_doc_1", "Redis TTL is 300 seconds.", source="Arch Spec")
    result = make_eval_result(chunks=[c1], decision=EvidenceDecision.SUFFICIENT)

    # Text has no bracket tags
    text = "The configured Redis cache TTL is 300 seconds."
    engine = CitationEngine()
    citations = engine.extract_citations(text, result)

    # Fallback attaches the strongest evidence chunk
    assert len(citations) == 1
    assert citations[0].chunk_id == "chunk_doc_1"
    assert citations[0].source_name == "Arch Spec"

