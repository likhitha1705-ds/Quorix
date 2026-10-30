"""Phase 3 Query Intelligence module."""
from __future__ import annotations

from app.intelligence.config import IntelligenceConfig, ScoringWeights
from app.intelligence.pipeline import QueryIntelligenceService
from app.intelligence.query_analysis import QueryAnalysisEngine
from app.intelligence.source_registry import SourceRegistryService
from app.intelligence.source_selection import SourceSelectionEngine
from app.schemas.intelligence import (
    QueryAnalysis,
    QueryAnalysisRequest,
    QueryAnalysisResponse,
    QueryDecision,
    QueryIntent,
    RankedSource,
    SourceMetadata,
)

__all__ = [
    "IntelligenceConfig",
    "ScoringWeights",
    "QueryIntelligenceService",
    "QueryAnalysisEngine",
    "SourceRegistryService",
    "SourceSelectionEngine",
    "QueryIntent",
    "QueryAnalysis",
    "QueryAnalysisRequest",
    "QueryAnalysisResponse",
    "QueryDecision",
    "RankedSource",
    "SourceMetadata",
]

