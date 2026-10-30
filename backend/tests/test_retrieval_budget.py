"""Unit tests for Step 1: Retrieval Budget Manager."""
from __future__ import annotations

import pytest

from app.retrieval.budget import RetrievalBudgetManager
from app.retrieval.config import RetrievalConfig
from app.schemas.intelligence import QueryAnalysis, QueryDecision, QueryIntent, RankedSource


def make_ranked_source(source_id: str, source_type: str, overall_score: float = 0.8) -> RankedSource:
    return RankedSource(
        source_id=source_id,
        source_name=f"Source {source_id}",
        source_type=source_type,
        relevance_score=0.8,
        authority_score=0.8,
        freshness_score=1.0,
        expected_directness_score=0.8,
        overall_score=overall_score,
        selection_reason="Selected",
        is_selected=True,
    )


def make_decision(selected: list[RankedSource]) -> QueryDecision:
    analysis = QueryAnalysis(
        query="Test query",
        intent=QueryIntent.TECHNICAL_EXPLANATION,
        keywords=["test"],
        entities=[],
        expected_information_type="technical_overview",
        preferred_sources=["documents"],
    )
    return QueryDecision(
        query_analysis=analysis,
        ranked_sources=selected,
        selected_sources=selected,
        skipped_sources=[],
        selection_reasons=["reason"],
    )


def test_budget_single_source_allocation():
    manager = RetrievalBudgetManager(RetrievalConfig(max_sources=3, max_chunks=10, max_context_tokens=4000, max_retrieval_calls=3))
    decision = make_decision([make_ranked_source("src_doc", "document")])

    plan = manager.create_plan(decision)
    assert plan.selected_sources == ["src_doc"]
    assert plan.chunk_limit == 10
    assert plan.token_limit == 4000
    assert plan.retrieval_call_limit == 1
    assert plan.retrieval_budget.allocated_chunks_per_source == {"src_doc": 10}
    assert plan.retrieval_budget.allocated_calls_per_source == {"src_doc": 1}


def test_budget_multi_source_allocation():
    manager = RetrievalBudgetManager(RetrievalConfig(max_sources=3, max_chunks=10, max_context_tokens=4000, max_retrieval_calls=3))
    sources = [
        make_ranked_source("src_conv", "conversation"),
        make_ranked_source("src_doc", "document"),
    ]
    decision = make_decision(sources)

    plan = manager.create_plan(decision)
    assert set(plan.selected_sources) == {"src_conv", "src_doc"}
    assert plan.chunk_limit == 10
    # 10 chunks split across 2 sources = 5 each
    assert plan.retrieval_budget.allocated_chunks_per_source["src_conv"] == 5
    assert plan.retrieval_budget.allocated_chunks_per_source["src_doc"] == 5
    assert plan.retrieval_call_limit == 2


def test_budget_max_sources_enforcement():
    # If 5 sources were passed, budget manager must cap to max_sources (3)
    manager = RetrievalBudgetManager(RetrievalConfig(max_sources=3, max_chunks=10))
    sources = [make_ranked_source(f"src_{i}", "document") for i in range(5)]
    decision = make_decision(sources)

    plan = manager.create_plan(decision)
    assert len(plan.selected_sources) == 3
    assert plan.retrieval_call_limit <= 3


def test_budget_empty_selection():
    manager = RetrievalBudgetManager()
    decision = make_decision([])

    plan = manager.create_plan(decision)
    assert plan.selected_sources == []
    assert plan.chunk_limit == 0
    assert plan.token_limit == 0
    assert plan.retrieval_call_limit == 0


def test_budget_tracking():
    manager = RetrievalBudgetManager()
    decision = make_decision([make_ranked_source("src_doc", "document")])
    plan = manager.create_plan(decision)

    usage = manager.track_usage(plan, chunks_retrieved=4, tokens_estimated=1200, calls_made=1)
    assert usage["chunks_used"] == 4
    assert usage["chunks_remaining"] == 6
    assert usage["tokens_used"] == 1200
    assert usage["tokens_remaining"] == 2800
    assert usage["calls_used"] == 1
    assert usage["budget_exhausted"] is False

