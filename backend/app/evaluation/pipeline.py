"""Evidence Intelligence Service orchestrating multi-criterion scoring, conflict detection, aggregation, and sufficiency decision."""
from __future__ import annotations

import logging
import time
from typing import Any

from app.evaluation.aggregation import EvidenceAggregator
from app.evaluation.config import EvaluationConfig
from app.evaluation.conflict_detection import ConflictDetector
from app.evaluation.scoring import EvidenceScoringEngine
from app.evaluation.sufficiency import SufficiencyChecker
from app.schemas.evaluation import EvaluatedChunk, EvidenceEvaluationResult
from app.schemas.retrieval import RetrievalResult

log = logging.getLogger(__name__)


class EvidenceIntelligenceService:
    """Core intelligence service for Phase 5: Evidence Intelligence & Sufficiency Evaluation."""

    def __init__(
        self,
        config: EvaluationConfig | None = None,
        scoring_engine: EvidenceScoringEngine | None = None,
        conflict_detector: ConflictDetector | None = None,
        aggregator: EvidenceAggregator | None = None,
        sufficiency_checker: SufficiencyChecker | None = None,
    ) -> None:
        self.config = config or EvaluationConfig()
        self.scoring_engine = scoring_engine or EvidenceScoringEngine(self.config)
        self.conflict_detector = conflict_detector or ConflictDetector()
        self.aggregator = aggregator or EvidenceAggregator()
        self.sufficiency_checker = sufficiency_checker or SufficiencyChecker(self.config)

    def evaluate(self, retrieval_result: RetrievalResult) -> EvidenceEvaluationResult:
        """Execute the complete Phase 5 pipeline on the retrieved context."""
        start_time = time.perf_counter()
        query_analysis = retrieval_result.query_analysis
        query_text = query_analysis.query

        # Step 14: Log incoming query
        log.info(
            "Starting evidence evaluation | query='%s' | intent=%s | chunks_count=%d",
            query_text,
            query_analysis.intent.value,
            len(retrieval_result.retrieved_chunks),
        )

        # 1. Multi-Criterion Evidence Scoring
        evaluated_chunks: list[EvaluatedChunk] = [
            self.scoring_engine.score_chunk(chunk, query_analysis)
            for chunk in retrieval_result.retrieved_chunks
        ]

        # Step 14: Log individual evidence scores
        for idx, ec in enumerate(evaluated_chunks, 1):
            log.info(
                "Chunk %d [%s] evaluated | score=%.2f (rel: %.2f, auth: %.2f, fresh: %.2f, dir: %.2f)",
                idx,
                ec.chunk_id,
                ec.score,
                ec.relevance_score,
                ec.authority_score,
                ec.freshness_score,
                ec.directness_score,
            )

        # 2. Conflict Detection
        conflicts = []
        if self.config.conflict_detection_enabled:
            conflicts = self.conflict_detector.detect(evaluated_chunks)

        # Step 14: Log conflicts detected
        if conflicts:
            log.warning(
                "Detected %d evidence conflicts across retrieved sources: %s",
                len(conflicts),
                [c.explanation for c in conflicts],
            )
        else:
            log.info("No factual conflicts detected across retrieved sources")

        # 3. Evidence Aggregation
        summary = self.aggregator.aggregate(evaluated_chunks, conflicts)

        # 4. Sufficiency Decision & Retrieval Loop Check
        decision, loop_decision, explanation = self.sufficiency_checker.evaluate(
            query_analysis=query_analysis,
            evaluated_chunks=evaluated_chunks,
            conflicts=conflicts,
            summary=summary,
            plan=retrieval_result.retrieval_plan,
            metrics=retrieval_result.retrieval_metrics,
        )

        overall_confidence = summary.highest_confidence if evaluated_chunks else 0.0

        duration_ms = (time.perf_counter() - start_time) * 1000.0

        # Step 14: Log confidence score, sufficiency decision, and execution time
        log.info(
            "Evidence evaluation completed | decision=%s | confidence=%.2f | needs_more_retrieval=%s | execution_time=%.2fms",
            decision.value,
            overall_confidence,
            loop_decision.needs_more_retrieval,
            duration_ms,
        )

        retrieval_metrics_dict = retrieval_result.retrieval_metrics.model_dump()
        execution_metadata: dict[str, Any] = {
            "evaluation_duration_ms": round(duration_ms, 2),
            "total_chunks_scored": len(evaluated_chunks),
            "conflicts_detected": len(conflicts),
            "sufficient_threshold": self.config.sufficient_threshold,
            "weights": self.config.weights.model_dump(),
        }

        return EvidenceEvaluationResult(
            query_analysis=query_analysis,
            evaluated_chunks=evaluated_chunks,
            evidence_summary=summary,
            conflicts=conflicts,
            confidence_score=round(overall_confidence, 4),
            evidence_decision=decision,
            needs_more_retrieval=loop_decision.needs_more_retrieval,
            remaining_budget=loop_decision.remaining_budget,
            evaluation_explanation=explanation,
            retrieval_metrics=retrieval_metrics_dict,
            execution_metadata=execution_metadata,
        )

