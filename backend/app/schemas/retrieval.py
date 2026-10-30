"""Schemas for Phase 4: Retrieval Budget Manager & Hybrid Retrieval Engine."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field, computed_field

from app.schemas.intelligence import QueryAnalysis, RankedSource


class RetrievalBudget(BaseModel):
    """Budget limits and source allocations computed by the Budget Manager."""

    max_sources: int = Field(default=3, ge=0)
    max_chunks: int = Field(default=10, ge=0)
    max_context_tokens: int = Field(default=4000, ge=0)
    max_retrieval_calls: int = Field(default=3, ge=0)
    allocated_chunks_per_source: dict[str, int] = Field(default_factory=dict)
    allocated_calls_per_source: dict[str, int] = Field(default_factory=dict)


class RetrievalPlan(BaseModel):
    """Actionable retrieval plan produced by the Budget Manager."""

    selected_sources: list[str] = Field(default_factory=list)
    retrieval_budget: RetrievalBudget
    chunk_limit: int = Field(default=10, ge=0)
    token_limit: int = Field(default=4000, ge=0)
    retrieval_call_limit: int = Field(default=3, ge=0)


class RetrievedChunk(BaseModel):
    """Normalized retrieved chunk model shared across all source types and engines."""

    chunk_id: str
    source_id: str
    source_type: str
    source_name: str
    content: str
    similarity_score: float = Field(default=0.0, ge=0.0, le=1.0)
    keyword_score: float = Field(default=0.0, ge=0.0, le=1.0)
    final_score: float = Field(default=0.0, ge=0.0, le=1.0)
    timestamp: datetime | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)

    @computed_field
    def source(self) -> str:
        """Convenience source display identifier required by Step 12."""
        return self.source_name or self.source_id

    @computed_field
    def score(self) -> float:
        """Convenience score alias to final_score required by Step 12."""
        return self.final_score

    def estimate_tokens(self, chars_per_token: float = 4.0) -> int:
        """Estimate token count for the content of this chunk."""
        if not self.content:
            return 0
        return max(1, int(len(self.content) / chars_per_token))


class RetrievalMetrics(BaseModel):
    """Operational metrics tracked during hybrid retrieval."""

    retrieval_calls: int = 0
    retrieved_chunks: int = 0
    selected_sources: list[str] = Field(default_factory=list)
    skipped_sources: list[str] = Field(default_factory=list)
    estimated_tokens: int = 0
    execution_time_ms: float = 0.0
    retrieval_budget_consumed: dict[str, Any] = Field(default_factory=dict)


class RetrievalResult(BaseModel):
    """Reusable output object produced by Phase 4, passed to Phase 5."""

    query_analysis: QueryAnalysis
    selected_sources: list[RankedSource] = Field(default_factory=list)
    retrieval_plan: RetrievalPlan
    retrieved_chunks: list[RetrievedChunk] = Field(default_factory=list)
    retrieval_metrics: RetrievalMetrics
    execution_metadata: dict[str, Any] = Field(default_factory=dict)

    def to_api_response(self) -> "RetrievalResponse":
        """Convert result object into the API response format specified in Step 12."""
        return RetrievalResponse(
            query_analysis=self.query_analysis.model_dump(),
            selected_sources=[s.model_dump() for s in self.selected_sources],
            retrieval_budget=self.retrieval_plan.retrieval_budget.model_dump(),
            retrieved_chunks=[c.model_dump() for c in self.retrieved_chunks],
            retrieval_metrics=self.retrieval_metrics.model_dump(),
        )


class RetrievalRequest(BaseModel):
    """Incoming request payload for POST /api/retrieve."""

    query: str = Field(
        ...,
        min_length=1,
        description="Natural language query to retrieve context for",
        examples=["Why was Redis caching introduced?"],
    )


class RetrievalResponse(BaseModel):
    """API response model for POST /api/retrieve matching Step 12."""

    query_analysis: dict[str, Any]
    selected_sources: list[dict[str, Any]]
    retrieval_budget: dict[str, Any]
    retrieved_chunks: list[dict[str, Any]]
    retrieval_metrics: dict[str, Any]
