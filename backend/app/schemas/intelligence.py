"""Schemas for Phase 3: Query Analysis & Intelligent Source Selection."""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, model_validator


class QueryIntent(str, Enum):
    """Supported query intents for intelligence routing."""

    TECHNICAL_EXPLANATION = "TECHNICAL_EXPLANATION"
    CONFIGURATION_LOOKUP = "CONFIGURATION_LOOKUP"
    HISTORICAL_REASON = "HISTORICAL_REASON"
    BUG_INVESTIGATION = "BUG_INVESTIGATION"
    FEATURE_INFORMATION = "FEATURE_INFORMATION"
    IMPLEMENTATION_DETAILS = "IMPLEMENTATION_DETAILS"
    GENERAL_INFORMATION = "GENERAL_INFORMATION"


class QueryAnalysisRequest(BaseModel):
    """Incoming request payload for query analysis."""

    query: str = Field(
        ...,
        min_length=1,
        description="Natural language query to analyze",
        examples=["Why was Redis caching introduced?"],
    )


class QueryAnalysis(BaseModel):
    """Structured output of the Query Analysis Engine."""

    query: str
    intent: QueryIntent
    keywords: list[str] = Field(default_factory=list)
    entities: list[str] = Field(default_factory=list)
    expected_information_type: str
    preferred_sources: list[str] = Field(default_factory=list)


class SourceMetadata(BaseModel):
    """Metadata representing an available knowledge source in the registry."""

    source_id: str
    source_name: str
    source_type: str
    description: str
    authority_score: float = Field(ge=0.0, le=1.0)
    last_updated: datetime
    supported_topics: list[str] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def _normalize_fields(cls, data: Any) -> Any:
        """Map database column names (name, authority_level, updated_at) if present."""
        if isinstance(data, dict):
            mapped = dict(data)
            if "name" in mapped and "source_name" not in mapped:
                mapped["source_name"] = mapped["name"]
            if "authority_level" in mapped and "authority_score" not in mapped:
                mapped["authority_score"] = float(mapped["authority_level"])
            if "updated_at" in mapped and "last_updated" not in mapped:
                mapped["last_updated"] = mapped["updated_at"]
            if "supported_topics" not in mapped or mapped["supported_topics"] is None:
                mapped["supported_topics"] = []
            return mapped
        return data


class RankedSource(BaseModel):
    """Individual source evaluated and scored for a specific query."""

    source_id: str
    source_name: str
    source_type: str
    relevance_score: float = Field(ge=0.0, le=1.0)
    authority_score: float = Field(ge=0.0, le=1.0)
    freshness_score: float = Field(ge=0.0, le=1.0)
    expected_directness_score: float = Field(ge=0.0, le=1.0)
    overall_score: float = Field(ge=0.0, le=1.0)
    selection_reason: str
    is_selected: bool


class QueryDecision(BaseModel):
    """Reusable output object produced by Phase 3, passed directly into Phase 4."""

    query_analysis: QueryAnalysis
    ranked_sources: list[RankedSource] = Field(default_factory=list)
    selected_sources: list[RankedSource] = Field(default_factory=list)
    skipped_sources: list[RankedSource] = Field(default_factory=list)
    selection_reasons: list[str] = Field(default_factory=list)
    retrieval_constraints: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

    def to_api_response(self) -> "QueryAnalysisResponse":
        """Convert decision object into the API response format."""
        return QueryAnalysisResponse(
            intent=self.query_analysis.intent.value,
            entities=self.query_analysis.entities,
            keywords=self.query_analysis.keywords,
            expected_information_type=self.query_analysis.expected_information_type,
            preferred_sources=self.query_analysis.preferred_sources,
            ranked_sources=self.ranked_sources,
            selected_sources=self.selected_sources,
            skipped_sources=self.skipped_sources,
            selection_reasons=self.selection_reasons,
            retrieval_constraints=self.retrieval_constraints,
            metadata=self.metadata,
        )


class QueryAnalysisResponse(BaseModel):
    """API response model for POST /api/query/analyze."""

    intent: str
    entities: list[str] = Field(default_factory=list)
    keywords: list[str] = Field(default_factory=list)
    expected_information_type: str | None = None
    preferred_sources: list[str] = Field(default_factory=list)
    ranked_sources: list[RankedSource] = Field(default_factory=list)
    selected_sources: list[RankedSource] = Field(default_factory=list)
    skipped_sources: list[RankedSource] = Field(default_factory=list)
    selection_reasons: list[str] = Field(default_factory=list)
    retrieval_constraints: dict[str, Any] = Field(default_factory=dict)
    metadata: dict[str, Any] = Field(default_factory=dict)

