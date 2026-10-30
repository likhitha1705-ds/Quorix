"""Configuration settings for Phase 4: Retrieval Budget Manager & Hybrid Retrieval."""
from __future__ import annotations

from pydantic import BaseModel, Field, model_validator


class RankingWeights(BaseModel):
    """Weights used by the RankingEngine to fuse semantic, keyword, authority, and freshness signals."""

    semantic: float = Field(default=0.50, ge=0.0, le=1.0)
    keyword: float = Field(default=0.30, ge=0.0, le=1.0)
    authority: float = Field(default=0.12, ge=0.0, le=1.0)
    freshness: float = Field(default=0.08, ge=0.0, le=1.0)

    @model_validator(mode="after")
    def _validate_weights(self) -> "RankingWeights":
        total = self.semantic + self.keyword + self.authority + self.freshness
        if not (0.98 <= total <= 1.02):
            raise ValueError(f"Ranking weights must sum to approximately 1.0 (got {total:.4f})")
        return self


class RetrievalConfig(BaseModel):
    """Runtime configuration for Phase 4 retrieval components."""

    # Budget limits (Step 1)
    max_sources: int = Field(default=3, ge=1)
    max_chunks: int = Field(default=10, ge=1)
    max_context_tokens: int = Field(default=4000, ge=100)
    max_retrieval_calls: int = Field(default=3, ge=1)

    # Ranking weights (Step 7)
    ranking_weights: RankingWeights = Field(default_factory=RankingWeights)

    # Candidate over-fetching multiplier before deduplication and context builder truncation
    candidate_pool_multiplier: int = Field(default=3, ge=1)

    # Token estimation heuristic
    chars_per_token: float = Field(default=4.0, gt=0.0)

    # Storage and collection settings
    qdrant_collection: str = "quorix_chunks"
    freshness_half_life_days: float = Field(default=180.0, gt=0.0)
    historical_penalty_discount: float = Field(default=0.25, ge=0.0, le=1.0)

