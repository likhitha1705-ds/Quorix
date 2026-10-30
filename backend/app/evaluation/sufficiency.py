"""Sufficiency checker and retrieval loop decision engine for Steps 9-11 of Phase 5.

Determines whether retrieved context is trustworthy, sufficient, conflicting, or unsupported,
and evaluates whether additional retrieval cycles are warranted by remaining budget.
"""
from __future__ import annotations

import logging
from typing import Any

from app.evaluation.config import EvaluationConfig
from app.schemas.evaluation import (
    Conflict,
    EvaluatedChunk,
    EvidenceDecision,
    EvidenceSummary,
    RetrievalLoopDecision,
)
from app.schemas.intelligence import QueryAnalysis
from app.schemas.retrieval import RetrievalMetrics, RetrievalPlan

log = logging.getLogger(__name__)


class SufficiencyChecker:
    """Evaluates evidence sufficiency, detects blocker conflicts, and decides retrieval continuation."""

    def __init__(self, config: EvaluationConfig | None = None) -> None:
        self.config = config or EvaluationConfig()

    def evaluate(
        self,
        query_analysis: QueryAnalysis,
        evaluated_chunks: list[EvaluatedChunk],
        conflicts: list[Conflict],
        summary: EvidenceSummary,
        plan: RetrievalPlan,
        metrics: RetrievalMetrics,
    ) -> tuple[EvidenceDecision, RetrievalLoopDecision, str]:
        """Produce the sufficiency decision, loop decision, and human-readable explanation."""
        # 1. Check for UNSUPPORTED
        if not evaluated_chunks or summary.highest_confidence < self.config.unsupported_threshold:
            decision = EvidenceDecision.UNSUPPORTED
            explanation = (
                f"Retrieved information is unsupported. No relevant sources or facts were found "
                f"matching query '{query_analysis.query}'."
            )
            loop_decision = self._check_retrieval_loop(decision, plan, metrics)
            return decision, loop_decision, explanation

        # 2. Check for CONFLICTING
        # Severe conflict condition: at least one high-severity conflict, or conflicts affecting
        # a substantial portion of evidence without an authoritative resolution
        high_severity_conflicts = [c for c in conflicts if c.severity == "high"]
        conflicting_chunk_count = len({cid for c in conflicts for cid in c.conflicting_chunks})
        conflict_ratio = conflicting_chunk_count / max(1, len(evaluated_chunks))

        if high_severity_conflicts or (conflicts and conflict_ratio >= self.config.conflict_dominance_ratio):
            decision = EvidenceDecision.CONFLICTING
            conflict_details = "; ".join(c.explanation for c in conflicts[:2])
            explanation = (
                f"Conflict detected across retrieved sources regarding {', '.join(high_severity_conflicts[0].conflicting_fields if high_severity_conflicts else conflicts[0].conflicting_fields)}. "
                f"{conflict_details}"
            )
            loop_decision = self._check_retrieval_loop(decision, plan, metrics)
            return decision, loop_decision, explanation

        # 3. Check for SUFFICIENT vs INSUFFICIENT
        # Sufficient requires highest confidence >= sufficient_threshold
        # and top chunk has non-negligible directness
        top_chunk = summary.strongest_evidence[0] if summary.strongest_evidence else None
        has_sufficient_score = (
            summary.highest_confidence >= self.config.sufficient_threshold
            or summary.average_confidence >= self.config.sufficient_threshold
        )
        has_direct_answer = top_chunk is not None and top_chunk.evidence_score.directness_score >= 0.50

        if has_sufficient_score and has_direct_answer:
            decision = EvidenceDecision.SUFFICIENT
            source_label = top_chunk.source if top_chunk else "retrieved sources"
            explanation = (
                f"Retrieved information is sufficient. {source_label} provides direct and authoritative "
                f"evidence answering '{query_analysis.query}' (confidence: {summary.highest_confidence:.2f})."
            )
        else:
            decision = EvidenceDecision.INSUFFICIENT
            if not has_direct_answer and top_chunk is not None:
                explanation = (
                    f"Retrieved information is insufficient. Sources mention query topics but lack "
                    f"a direct, definitive answer to '{query_analysis.query}'."
                )
            else:
                explanation = (
                    f"Retrieved information is insufficient. Evidence confidence "
                    f"({summary.highest_confidence:.2f}) falls below the sufficiency threshold "
                    f"({self.config.sufficient_threshold:.2f})."
                )

        loop_decision = self._check_retrieval_loop(decision, plan, metrics)
        return decision, loop_decision, explanation

    def _check_retrieval_loop(
        self,
        decision: EvidenceDecision,
        plan: RetrievalPlan,
        metrics: RetrievalMetrics,
    ) -> RetrievalLoopDecision:
        """Evaluate whether retrieval budget permits further searches (Step 10)."""
        total_max_calls = max(plan.retrieval_call_limit, plan.retrieval_budget.max_retrieval_calls)
        total_max_chunks = max(plan.chunk_limit, plan.retrieval_budget.max_chunks)
        total_max_tokens = max(plan.token_limit, plan.retrieval_budget.max_context_tokens)

        chunks_remaining = max(0, total_max_chunks - metrics.retrieved_chunks)
        calls_remaining = max(0, total_max_calls - metrics.retrieval_calls)
        tokens_remaining = max(0, total_max_tokens - metrics.estimated_tokens)

        remaining_budget: dict[str, Any] = {
            "chunks_remaining": chunks_remaining,
            "calls_remaining": calls_remaining,
            "tokens_remaining": tokens_remaining,
            "chunk_limit": total_max_chunks,
            "call_limit": total_max_calls,
            "token_limit": total_max_tokens,
        }

        if decision == EvidenceDecision.SUFFICIENT:
            return RetrievalLoopDecision(
                needs_more_retrieval=False,
                remaining_budget=remaining_budget,
                reason="Evidence is sufficient to answer query; no further retrieval required.",
            )

        # For INSUFFICIENT, CONFLICTING, or UNSUPPORTED:
        has_budget = chunks_remaining > 0 and calls_remaining > 0 and tokens_remaining > 100

        if has_budget:
            reason = (
                f"Decision is {decision.value}; retrieval budget has capacity for additional searches "
                f"({chunks_remaining} chunks, {calls_remaining} calls remaining)."
            )
            return RetrievalLoopDecision(
                needs_more_retrieval=True,
                remaining_budget=remaining_budget,
                reason=reason,
            )
        else:
            reason = (
                f"Decision is {decision.value}, but retrieval budget is exhausted "
                f"(calls remaining: {calls_remaining}, chunks remaining: {chunks_remaining})."
            )
            return RetrievalLoopDecision(
                needs_more_retrieval=False,
                remaining_budget=remaining_budget,
                reason=reason,
            )
