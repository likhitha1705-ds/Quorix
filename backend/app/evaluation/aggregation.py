"""Evidence aggregation engine for Step 8 of Phase 5.

Synthesizes metrics, confidence extrema, strongest evidence rankings,
and source attribution across all evaluated chunks and detected conflicts.
"""
from __future__ import annotations

import logging

from app.schemas.evaluation import Conflict, EvaluatedChunk, EvidenceSummary

log = logging.getLogger(__name__)


class EvidenceAggregator:
    """Aggregates evaluated chunk scores and compiles evidence metrics."""

    def aggregate(
        self,
        evaluated_chunks: list[EvaluatedChunk],
        conflicts: list[Conflict],
        top_k_strongest: int = 5,
    ) -> EvidenceSummary:
        """Calculate evidence summary statistics and source categorization."""
        if not evaluated_chunks:
            return EvidenceSummary(
                average_confidence=0.0,
                highest_confidence=0.0,
                lowest_confidence=0.0,
                total_evaluated_chunks=0,
                strongest_evidence=[],
                supporting_sources=[],
                conflicting_sources=[],
            )

        confidences = [c.score for c in evaluated_chunks]
        avg_conf = round(sum(confidences) / len(confidences), 4)
        highest_conf = round(max(confidences), 4)
        lowest_conf = round(min(confidences), 4)

        # Sort chunks descending by confidence score
        sorted_chunks = sorted(evaluated_chunks, key=lambda c: c.score, reverse=True)
        strongest_evidence = sorted_chunks[:top_k_strongest]

        # Identify sources involved in conflicts
        conflicting_chunk_ids = {
            cid for conflict in conflicts for cid in conflict.conflicting_chunks
        }

        conflicting_sources_set: set[str] = set()
        supporting_sources_set: set[str] = set()

        for chunk in evaluated_chunks:
            source_label = chunk.source
            if chunk.chunk_id in conflicting_chunk_ids:
                conflicting_sources_set.add(source_label)
            else:
                supporting_sources_set.add(source_label)

        return EvidenceSummary(
            average_confidence=avg_conf,
            highest_confidence=highest_conf,
            lowest_confidence=lowest_conf,
            total_evaluated_chunks=len(evaluated_chunks),
            strongest_evidence=strongest_evidence,
            supporting_sources=sorted(supporting_sources_set),
            conflicting_sources=sorted(conflicting_sources_set),
        )

