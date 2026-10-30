"""Metrics tracking for Phase 4 retrieval execution."""
from __future__ import annotations

from typing import Any

from app.schemas.retrieval import RetrievalMetrics, RetrievalPlan


class RetrievalMetricsTracker:
    """Collects and aggregates operational metrics across retrieval stages."""

    @staticmethod
    def build_metrics(
        plan: RetrievalPlan,
        calls_made: int,
        chunks_retrieved: int,
        estimated_tokens: int,
        execution_time_ms: float,
        selected_sources: list[str],
        skipped_sources: list[str],
    ) -> RetrievalMetrics:
        """Create structured RetrievalMetrics object."""
        budget_consumed = {
            "chunks_used": chunks_retrieved,
            "chunks_limit": plan.chunk_limit,
            "chunks_remaining": max(0, plan.chunk_limit - chunks_retrieved),
            "tokens_used": estimated_tokens,
            "tokens_limit": plan.token_limit,
            "tokens_remaining": max(0, plan.token_limit - estimated_tokens),
            "calls_used": calls_made,
            "calls_limit": plan.retrieval_call_limit,
            "calls_remaining": max(0, plan.retrieval_call_limit - calls_made),
            "budget_exhausted": (
                (plan.chunk_limit > 0 and chunks_retrieved >= plan.chunk_limit)
                or (plan.token_limit > 0 and estimated_tokens >= plan.token_limit)
            ),
        }

        return RetrievalMetrics(
            retrieval_calls=calls_made,
            retrieved_chunks=chunks_retrieved,
            selected_sources=selected_sources,
            skipped_sources=skipped_sources,
            estimated_tokens=estimated_tokens,
            execution_time_ms=execution_time_ms,
            retrieval_budget_consumed=budget_consumed,
        )
