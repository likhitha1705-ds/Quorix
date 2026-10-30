"""Configuration settings for Phase 5: Evidence Intelligence & Sufficiency Evaluation."""
from __future__ import annotations

from pydantic import BaseModel, Field, model_validator


class EvidenceScoringWeights(BaseModel):
    """Configurable weights for multi-criterion evidence scoring."""

    relevance: float = Field(default=0.40, ge=0.0, le=1.0)
    authority: float = Field(default=0.25, ge=0.0, le=1.0)
    directness: float = Field(default=0.20, ge=0.0, le=1.0)
    freshness: float = Field(default=0.15, ge=0.0, le=1.0)

    @model_validator(mode="after")
    def _validate_weights(self) -> "EvidenceScoringWeights":
        total = self.relevance + self.authority + self.directness + self.freshness
        if not (0.98 <= total <= 1.02):
            raise ValueError(f"Evidence scoring weights must sum to approximately 1.0 (got {total:.4f})")
        return self


class EvaluationConfig(BaseModel):
    """Runtime configuration for Phase 5 evaluation engine."""

    weights: EvidenceScoringWeights = Field(default_factory=EvidenceScoringWeights)
    sufficient_threshold: float = Field(default=0.65, ge=0.0, le=1.0)
    unsupported_threshold: float = Field(default=0.20, ge=0.0, le=1.0)
    conflict_dominance_ratio: float = Field(default=0.50, ge=0.0, le=1.0)
    freshness_half_life_days: float = Field(default=180.0, gt=0.0)
    historical_penalty_discount: float = Field(default=0.25, ge=0.0, le=1.0)
    conflict_detection_enabled: bool = True

