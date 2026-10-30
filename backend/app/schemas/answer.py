"""Schemas for Phase 6: Answer Generation & Citation Engine."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from app.schemas.evaluation import EvidenceDecision


class Citation(BaseModel):
    """Structured attribution referencing an evidence chunk supporting an assertion."""

    chunk_id: str = Field(description="Unique identifier of the cited chunk")
    source_name: str = Field(description="Display name of the cited knowledge source")
    source_type: str = Field(description="Type of the knowledge source (document, conversation, ticket)")
    source_id: str = Field(default="", description="Source repository identifier")
    quote: str | None = Field(default=None, description="Direct relevant quote or excerpt from the chunk")
    confidence_score: float = Field(default=0.0, ge=0.0, le=1.0, description="Confidence score of the evidence chunk")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Metadata associated with the chunk")


class AnswerExecutionMetrics(BaseModel):
    """Operational and LLM metrics recorded during answer generation."""

    llm_latency_ms: float = Field(default=0.0, description="Latency of LLM invocation in milliseconds")
    prompt_tokens: int = Field(default=0, description="Tokens consumed by the prompt")
    completion_tokens: int = Field(default=0, description="Tokens produced by the model")
    total_tokens: int = Field(default=0, description="Total tokens consumed")
    estimated_cost: float = Field(default=0.0, description="Estimated inference cost in USD")
    response_generation_time_ms: float = Field(default=0.0, description="Total answer pipeline execution time in ms")
    retrieval_metrics: dict[str, Any] = Field(default_factory=dict, description="Upstream retrieval operational metrics")


class AnswerResult(BaseModel):
    """Reusable domain object produced by Phase 6, directly consumable by frontend chatbot."""

    answer: str = Field(description="Natural language evidence-grounded answer")
    summary: str = Field(description="Concise one-paragraph summary of the findings")
    citations: list[Citation] = Field(default_factory=list, description="Validated citations supporting the answer")
    confidence: float = Field(ge=0.0, le=1.0, description="Aggregated confidence score from Phase 5")
    evidence_decision: EvidenceDecision = Field(description="Sufficiency status: SUFFICIENT, INSUFFICIENT, CONFLICTING, UNSUPPORTED")
    reasoning: str = Field(description="Evaluation explanation detailing evidence trustworthiness and decisions")
    execution_metrics: AnswerExecutionMetrics = Field(description="Comprehensive execution metrics")

    def to_api_response(self) -> "AnswerResponse":
        """Format domain model into Step 6 API response structure."""
        return AnswerResponse(
            answer=self.answer,
            summary=self.summary,
            citations=[c.model_dump() for c in self.citations],
            confidence=round(self.confidence, 4),
            decision=self.evidence_decision.value,
            reasoning=self.reasoning,
            execution_metrics=self.execution_metrics.model_dump(),
        )


class AnswerRequest(BaseModel):
    """Incoming request payload for POST /api/answer."""

    query: str = Field(
        ...,
        min_length=1,
        description="Natural language question to retrieve, evaluate, and generate an answer for",
        examples=["Why was Redis caching introduced?"],
    )


class AnswerResponse(BaseModel):
    """API response model for POST /api/answer matching Step 6 format."""

    answer: str
    summary: str
    citations: list[dict[str, Any]] = Field(default_factory=list)
    confidence: float
    decision: str
    reasoning: str
    execution_metrics: dict[str, Any] = Field(default_factory=dict)

