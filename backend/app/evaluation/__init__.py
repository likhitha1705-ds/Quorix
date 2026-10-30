"""Phase 5: Evidence Intelligence & Sufficiency Evaluation package."""
from __future__ import annotations

from app.evaluation.aggregation import EvidenceAggregator
from app.evaluation.config import EvaluationConfig, EvidenceScoringWeights
from app.evaluation.conflict_detection import ConflictDetector
from app.evaluation.pipeline import EvidenceIntelligenceService
from app.evaluation.scoring import (
    AuthorityEvaluator,
    DirectnessEvaluator,
    EvidenceScoringEngine,
    FreshnessEvaluator,
    RelevanceEvaluator,
)
from app.evaluation.sufficiency import SufficiencyChecker

__all__ = [
    "AuthorityEvaluator",
    "ConflictDetector",
    "DirectnessEvaluator",
    "EvaluationConfig",
    "EvidenceAggregator",
    "EvidenceIntelligenceService",
    "EvidenceScore",
    "EvidenceScoringEngine",
    "EvidenceScoringWeights",
    "FreshnessEvaluator",
    "RelevanceEvaluator",
    "SufficiencyChecker",
]

