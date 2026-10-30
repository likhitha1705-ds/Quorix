"""API routes for Query Intelligence and Source Selection."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from app.core.config import get_settings
from app.intelligence.config import IntelligenceConfig, ScoringWeights
from app.intelligence.pipeline import QueryIntelligenceService
from app.schemas.intelligence import QueryAnalysisRequest, QueryAnalysisResponse

router = APIRouter(prefix="/query", tags=["query"])


def get_query_intelligence_service() -> QueryIntelligenceService:
    """Dependency provider for the QueryIntelligenceService with app settings."""
    settings = get_settings()
    weights = ScoringWeights(
        relevance=settings.relevance_weight,
        authority=settings.authority_weight,
        freshness=settings.freshness_weight,
        directness=settings.directness_weight,
    )
    config = IntelligenceConfig(
        weights=weights,
        confidence_threshold=settings.confidence_threshold,
        min_relevance_threshold=settings.min_relevance_threshold,
        max_selected_sources=settings.max_selected_sources,
        freshness_half_life_days=settings.freshness_half_life_days,
        historical_penalty_discount=settings.historical_freshness_discount,
    )
    return QueryIntelligenceService(config=config)


@router.post("", response_model=QueryAnalysisResponse)
@router.post("/analyze", response_model=QueryAnalysisResponse)
def analyze_query(
    request: QueryAnalysisRequest,
    service: QueryIntelligenceService = Depends(get_query_intelligence_service),
) -> QueryAnalysisResponse:
    """Analyze a user query and determine ranked and selected knowledge sources without document retrieval."""
    decision = service.analyze_and_select(request.query)
    return decision.to_api_response()
