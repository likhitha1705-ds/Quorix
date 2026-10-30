"""Retrieval Budget Manager: allocates retrieval budget and limits retrieval calls, chunks, and tokens."""
from __future__ import annotations

import logging
from typing import Any

from app.retrieval.config import RetrievalConfig
from app.schemas.intelligence import QueryDecision
from app.schemas.retrieval import RetrievalBudget, RetrievalPlan

log = logging.getLogger(__name__)


class RetrievalBudgetManager:
    """Allocates and monitors retrieval budget according to configured limits and Phase 3 decision."""

    def __init__(self, config: RetrievalConfig | None = None) -> None:
        self.config = config or RetrievalConfig()

    def create_plan(self, decision: QueryDecision) -> RetrievalPlan:
        """Create an actionable RetrievalPlan given the selected sources in QueryDecision."""
        selected_candidates = decision.selected_sources
        if not selected_candidates:
            log.info("No sources selected by Phase 3; creating empty retrieval plan")
            empty_budget = RetrievalBudget(
                max_sources=self.config.max_sources,
                max_chunks=0,
                max_context_tokens=0,
                max_retrieval_calls=0,
                allocated_chunks_per_source={},
                allocated_calls_per_source={},
            )
            return RetrievalPlan(
                selected_sources=[],
                retrieval_budget=empty_budget,
                chunk_limit=0,
                token_limit=0,
                retrieval_call_limit=0,
            )

        # Enforce maximum sources limit
        active_sources = selected_candidates[: self.config.max_sources]
        selected_source_ids = [s.source_id for s in active_sources]
        num_sources = len(active_sources)

        # Decide chunk allocations across selected sources
        allocated_chunks: dict[str, int] = {}
        base_chunk_allocation = self.config.max_chunks // num_sources
        remainder = self.config.max_chunks % num_sources

        for i, src in enumerate(active_sources):
            extra = 1 if i < remainder else 0
            allocated_chunks[src.source_id] = max(1, base_chunk_allocation + extra)

        # Decide retrieval calls allocation (1 retrieval call per source up to max_retrieval_calls)
        allocated_calls: dict[str, int] = {}
        max_calls_to_distribute = min(num_sources, self.config.max_retrieval_calls)
        for i, src in enumerate(active_sources):
            allocated_calls[src.source_id] = 1 if i < max_calls_to_distribute else 0

        call_limit = min(sum(allocated_calls.values()), self.config.max_retrieval_calls)

        budget = RetrievalBudget(
            max_sources=self.config.max_sources,
            max_chunks=self.config.max_chunks,
            max_context_tokens=self.config.max_context_tokens,
            max_retrieval_calls=self.config.max_retrieval_calls,
            allocated_chunks_per_source=allocated_chunks,
            allocated_calls_per_source=allocated_calls,
        )

        plan = RetrievalPlan(
            selected_sources=selected_source_ids,
            retrieval_budget=budget,
            chunk_limit=self.config.max_chunks,
            token_limit=self.config.max_context_tokens,
            retrieval_call_limit=call_limit,
        )

        log.debug(
            "Created RetrievalPlan: %d sources selected, %d chunk limit, %d call limit",
            len(selected_source_ids),
            plan.chunk_limit,
            plan.retrieval_call_limit,
        )
        return plan

    def track_usage(
        self,
        plan: RetrievalPlan,
        chunks_retrieved: int,
        tokens_estimated: int,
        calls_made: int,
    ) -> dict[str, Any]:
        """Track retrieval consumption against the allocated plan."""
        return {
            "chunks_used": chunks_retrieved,
            "chunks_limit": plan.chunk_limit,
            "chunks_remaining": max(0, plan.chunk_limit - chunks_retrieved),
            "tokens_used": tokens_estimated,
            "tokens_limit": plan.token_limit,
            "tokens_remaining": max(0, plan.token_limit - tokens_estimated),
            "calls_used": calls_made,
            "calls_limit": plan.retrieval_call_limit,
            "calls_remaining": max(0, plan.retrieval_call_limit - calls_made),
            "budget_exhausted": (
                (plan.chunk_limit > 0 and chunks_retrieved >= plan.chunk_limit)
                or (plan.token_limit > 0 and tokens_estimated >= plan.token_limit)
            ),
        }
