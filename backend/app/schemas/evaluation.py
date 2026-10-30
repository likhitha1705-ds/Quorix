"""Schemas for Phase 5: Evidence Intelligence & Sufficiency Evaluation."""
from __future__ import annotations

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, computed_field

from app.schemas.intelligence import QueryAnalysis
from app.schemas.retrieval import RetrievedChunk


class EvidenceDecision(str, Enum):
    """Categorical sufficiency decision produced by the Sufficiency Checker."""

    SUFFICIENT = "SUFFICIENT"
    INSUFFICIENT = "INSUFFICIENT"
    CONFLICTING = "CONFLICTING"
    UNSUPPORTED = "UNSUPPORTED"


class EvidenceScore(BaseModel):
    """Normalized multi-criterion evaluation scores for an individual retrieved chunk."""

    relevance_score: float = Field(ge=0.0, le=1.0)
    authority_score: float = Field(ge=0.0, le=1.0)
    freshness_score: float = Field(ge=0.0, le=1.0)
    directness_score: float = Field(ge=0.0, le=1.0)
    confidence_score: float = Field(ge=0.0, le=1.0)
    explanation: str


class EvaluatedChunk(BaseModel):
    """Retrieved chunk augmented with comprehensive evidence evaluation scores."""

    chunk: RetrievedChunk
    evidence_score: EvidenceScore

    @computed_field
    def chunk_id(self) -> str:
        return self.chunk.chunk_id

    @computed_field
    def source(self) -> str:
        return self.chunk.source

    @computed_field
    def score(self) -> float:
        return round(self.evidence_score.confidence_score, 4)

    @computed_field
    def relevance_score(self) -> float:
        return round(self.evidence_score.relevance_score, 4)

    @computed_field
    def authority_score(self) -> float:
        return round(self.evidence_score.authority_score, 4)

    @computed_field
    def freshness_score(self) -> float:
        return round(self.evidence_score.freshness_score, 4)

    @computed_field
    def directness_score(self) -> float:
        return round(self.evidence_score.directness_score, 4)

    @computed_field
    def confidence_score(self) -> float:
        return round(self.evidence_score.confidence_score, 4)

    @computed_field
    def explanation(self) -> str:
        return self.evidence_score.explanation

    @computed_field
    def content(self) -> str:
        return self.chunk.content

    @computed_field
    def metadata(self) -> dict[str, Any]:
        return self.chunk.metadata

    @computed_field
    def source_id(self) -> str:
        return self.chunk.source_id

    @computed_field
    def source_type(self) -> str:
        return self.chunk.source_type

    def to_api_dict(self) -> dict[str, Any]:
        """Format chunk for Step 12 API response."""
        return {
            "chunk_id": self.chunk_id,
            "source": self.source,
            "score": self.score,
            "relevance_score": self.relevance_score,
            "authority_score": self.authority_score,
            "freshness_score": self.freshness_score,
            "directness_score": self.directness_score,
            "confidence_score": self.confidence_score,
            "explanation": self.explanation,
            "content": self.content,
            "metadata": self.metadata,
        }


class Conflict(BaseModel):
    """Represents a detected contradiction or factual divergence between retrieved chunks."""

    conflicting_chunks: list[str] = Field(default_factory=list, description="IDs of chunks that conflict")
    conflicting_fields: list[str] = Field(default_factory=list, description="Parameters or topics in conflict")
    severity: str = Field(default="medium", description="'low', 'medium', or 'high'")
    explanation: str


class EvidenceSummary(BaseModel):
    """Aggregated assessment across all evaluated chunks."""

    average_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    highest_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    lowest_confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    total_evaluated_chunks: int = 0
    strongest_evidence: list[EvaluatedChunk] = Field(default_factory=list)
    supporting_sources: list[str] = Field(default_factory=list)
    conflicting_sources: list[str] = Field(default_factory=list)


class RetrievalLoopDecision(BaseModel):
    """Decision indicating whether further retrieval iterations are warranted."""

    needs_more_retrieval: bool
    remaining_budget: dict[str, Any] = Field(default_factory=dict)
    reason: str


class EvidenceEvaluationResult(BaseModel):
    """Reusable output object produced by Phase 5, passed to Phase 6."""

    query_analysis: QueryAnalysis
    evaluated_chunks: list[EvaluatedChunk] = Field(default_factory=list)
    evidence_summary: EvidenceSummary
    conflicts: list[Conflict] = Field(default_factory=list)
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0)
    evidence_decision: EvidenceDecision
    needs_more_retrieval: bool
    remaining_budget: dict[str, Any] = Field(default_factory=dict)
    evaluation_explanation: str
    retrieval_metrics: dict[str, Any] = Field(default_factory=dict)
    execution_metadata: dict[str, Any] = Field(default_factory=dict)

    def to_api_response(self) -> "EvidenceEvaluationResponse":
        """Convert evaluation result into the API response format specified in Step 13."""
        return EvidenceEvaluationResponse(
            evaluated_chunks=[c.to_api_dict() for c in self.evaluated_chunks],
            evidence_summary=self.evidence_summary.model_dump(),
            conflicts=[con.model_dump() for con in self.conflicts],
            confidence=round(self.confidence_score, 4),
            decision=self.evidence_decision.value,
            needs_more_retrieval=self.needs_more_retrieval,
            evaluation_explanation=self.evaluation_explanation,
            retrieval_metrics=self.retrieval_metrics,
        )


class EvidenceEvaluationRequest(BaseModel):
    """Incoming request payload for POST /api/evaluate."""

    query: str = Field(
        ...,
        min_length=1,
        description="Natural language query to retrieve and evaluate evidence for",
        examples=["Why was Redis caching introduced?"],
    )


class EvidenceEvaluationResponse(BaseModel):
    """API response model for POST /api/evaluate matching Step 13."""

    evaluated_chunks: list[dict[str, Any]] = Field(default_factory=list)
    evidence_summary: dict[str, Any]
    conflicts: list[dict[str, Any]] = Field(default_factory=list)
    confidence: float
    decision: str
    needs_more_retrieval: bool
    evaluation_explanation: str
    retrieval_metrics: dict[str, Any] = Field(default_factory=dict)
